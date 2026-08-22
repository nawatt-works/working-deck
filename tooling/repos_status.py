#!/usr/bin/env python3
"""Report cross-repository state for every workspace repository.

Workspace root ไม่สามารถตอบได้ว่างานใน repos/ ถูกบันทึกแล้วหรือยัง เพราะเนื้อหา
ใต้ repos/ ถูก ignore จาก root Git repository เครื่องมือนี้กวาดทุก repo แล้วรายงาน
สามอย่างที่ root มองไม่เห็น:

1. สถานะ Git ของแต่ละ repo — branch, การเปลี่ยนแปลงค้าง, ahead/behind
2. tracking state — repo นั้นถูกบันทึกไว้ที่ใดที่หนึ่งจริงหรือไม่
3. AI artifact ที่กำลังจะถูก commit เข้า repository ภายนอกโดยไม่ตั้งใจ
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from .repository_catalog import (
        CatalogError,
        discover_repository_paths,
        load_catalog,
    )
except ImportError:
    from repository_catalog import (  # type: ignore[no-redef]
        CatalogError,
        discover_repository_paths,
        load_catalog,
    )


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "workspace-meta" / "repositories.yaml"

# ไฟล์และโฟลเดอร์ที่เป็น coordination artifact ของ root workspace
# การพบสิ่งเหล่านี้ใน change set ของ repository ภายนอกถือว่าผิดปกติเสมอ
ARTIFACT_NAMES = frozenset(
    {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GIT_POLICY.md"}
)
ARTIFACT_DIRS = frozenset({".agents", ".claude", "workspace-meta", "workbench"})

STATE_OK_EXTERNAL = "external"
STATE_OK_INTERNAL = "internal"
STATE_GITLINK = "gitlink"
STATE_UNTRACKED = "untracked"
STATE_MISSING = "missing"


def run_git(cwd: Path, *args: str) -> str | None:
    """Run a Git command and return stripped stdout, or None when it fails."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def is_ignored_by_root(relative_path: str) -> bool:
    """Return whether the root repository ignores the given workspace path."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", relative_path],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def classify(has_own_git: bool, ignored: bool) -> str:
    if has_own_git and ignored:
        return STATE_OK_EXTERNAL
    if not has_own_git and not ignored:
        return STATE_OK_INTERNAL
    if has_own_git and not ignored:
        return STATE_GITLINK
    return STATE_UNTRACKED


def porcelain_entries(repo: Path) -> list[tuple[str, str]]:
    """Return (status_code, path) for every pending change in a repository."""
    output = run_git(repo, "status", "--porcelain")
    if not output:
        return []
    entries = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:]
        # rename entries look like "old -> new"; the destination is what ships
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        entries.append((code, path.strip('"')))
    return entries


def artifact_hits(entries: list[tuple[str, str]]) -> list[str]:
    """Return pending paths that look like root workspace coordination artifacts.

    ตรวจเฉพาะไฟล์ที่ยัง pending เพราะไฟล์ที่ commit ไปแล้วเป็นของ repository นั้น
    เช่น AI harness configuration ที่ทีมของลูกค้าใช้อยู่ ซึ่งไม่ใช่การรั่วไหล
    """
    hits = []
    for _code, path in entries:
        parts = Path(path).parts
        if not parts:
            continue
        if parts[-1] in ARTIFACT_NAMES or any(p in ARTIFACT_DIRS for p in parts):
            hits.append(path)
    return sorted(set(hits))


def git_summary(repo: Path) -> str:
    branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD") or "?"
    entries = porcelain_entries(repo)
    staged = sum(1 for code, _ in entries if code[0] not in " ?")
    unstaged = sum(1 for code, _ in entries if code[1] not in " ?")
    untracked = sum(1 for code, _ in entries if code == "??")

    parts = [branch]
    if staged:
        parts.append(f"staged:{staged}")
    if unstaged:
        parts.append(f"unstaged:{unstaged}")
    if untracked:
        parts.append(f"untracked:{untracked}")

    counts = run_git(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    if counts:
        ahead, _, behind = counts.partition("\t")
        if ahead.strip() != "0":
            parts.append(f"ahead:{ahead.strip()}")
        if behind.strip() != "0":
            parts.append(f"behind:{behind.strip()}")
    else:
        parts.append("no-upstream")

    if not any(p.startswith(("staged", "unstaged", "untracked")) for p in parts):
        parts.append("clean")
    return "  ".join(parts)


def inspect(relative_path: str) -> dict[str, object]:
    directory = ROOT / relative_path
    if not directory.is_dir():
        return {"path": relative_path, "state": STATE_MISSING}

    has_own_git = (directory / ".git").exists()
    state = classify(has_own_git, is_ignored_by_root(relative_path))
    record: dict[str, object] = {"path": relative_path, "state": state}

    if has_own_git:
        record["summary"] = git_summary(directory)
        record["artifacts"] = artifact_hits(porcelain_entries(directory))
    return record


def main() -> int:
    try:
        repositories = load_catalog(CATALOG)
        cataloged = {entry["path"] for entry in repositories}
        discovered = discover_repository_paths(ROOT)
    except (CatalogError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    for relative_path in sorted(cataloged | discovered):
        record = inspect(relative_path)
        state = record["state"]
        label = f"{state:<9} {relative_path}"

        if state == STATE_MISSING:
            print(f"{label}  ยังไม่มี checkout บนเครื่องนี้")
            warnings.append(f"{relative_path}: cataloged แต่ยังไม่ได้ clone")
            continue

        if relative_path not in cataloged:
            warnings.append(
                f"{relative_path}: ยังไม่มีใน Catalog ใช้ $manage-repository-catalog เพิ่ม"
            )

        if state == STATE_OK_EXTERNAL:
            print(f"{label}  {record['summary']}")
        elif state == STATE_OK_INTERNAL:
            print(f"{label}  ถูก track ใน root Git repository")
        elif state == STATE_GITLINK:
            print(f"{label}  {record['summary']}")
            errors.append(
                f"{relative_path}: มี .git ของตัวเองแต่ root ไม่ได้ ignore "
                f"หาก commit จะกลายเป็น gitlink ที่ clone แล้วว่างเปล่า "
                f"ให้ลบบรรทัด opt-in ของ path นี้ออกจาก .gitignore"
            )
        elif state == STATE_UNTRACKED:
            print(f"{label}  ไม่มี .git ของตัวเอง และถูก root ignore")
            errors.append(
                f"{relative_path}: งานในโฟลเดอร์นี้ไม่ถูก track ที่ใดเลย "
                f"ให้ opt-in ด้วย '!{relative_path}/' ใน .gitignore "
                f"หรือทำให้เป็น Git repository ของตัวเอง"
            )

        for hit in record.get("artifacts") or []:
            errors.append(
                f"{relative_path}: พบ coordination artifact ค้างอยู่ใน change set "
                f"— {hit} ห้าม commit เข้า repository ภายนอก"
            )

    if not (cataloged | discovered):
        print("ยังไม่มี repository ใน workspace")

    # ให้ตารางสถานะออกก่อนเสมอ เพื่อให้อ่านคู่กับ warning และ error ที่อ้างถึงมันได้
    sys.stdout.flush()

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
