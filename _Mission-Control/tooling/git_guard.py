#!/usr/bin/env python3
"""Inspect workspace repositories and guard remote Git writes.

Working Deck keeps independent Git repositories as direct children of ``repos/``.
Every repository is treated as ``client`` unless its path is explicitly listed in
``_Mission-Control/git-safety.yaml``.  The optional pre-push hook calls this module
so the same guard applies whether Git is invoked by a person, Pi, Codex, Claude,
or another tool.
"""

from __future__ import annotations

import argparse
import json
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORIES_ROOT = WORKSPACE_ROOT / "repos"
CONFIG_PATH = WORKSPACE_ROOT / "_Mission-Control" / "git-safety.yaml"
HOOK_TEMPLATE_PATH = WORKSPACE_ROOT / "_Mission-Control" / "hooks" / "pre-push"
HOOK_MARKER = "# Working Deck Git guard"

ARTIFACT_NAMES = frozenset(
    {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GIT_POLICY.md"}
)
ARTIFACT_DIRS = frozenset({".agents", ".claude", "_Mission-Control"})
KEY_VALUE_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


class SafetyError(ValueError):
    """Raised when Git safety configuration or repository state is invalid."""


@dataclass(frozen=True)
class SafetyConfig:
    own_repositories: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryInfo:
    relative_path: str
    path: Path
    common_dir: Path
    repository_class: str


def _parse_scalar(value: str, line_number: int) -> str:
    value = value.strip()
    if not value:
        raise SafetyError(f"line {line_number}: expected a scalar value")
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise SafetyError(f"line {line_number}: invalid quoted value") from error
        if not isinstance(parsed, str):
            raise SafetyError(f"line {line_number}: expected a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise SafetyError(f"line {line_number}: invalid quoted value")
        return value[1:-1].replace("''", "'")
    scalar = value.split(" #", 1)[0].strip()
    if not scalar:
        raise SafetyError(f"line {line_number}: expected a scalar value")
    return scalar


def _validate_repository_path(value: str, line_number: int | None = None) -> str:
    path = PurePosixPath(value)
    prefix = f"line {line_number}: " if line_number is not None else ""
    if path.is_absolute() or ".." in path.parts:
        raise SafetyError(f"{prefix}repository path must be workspace-relative")
    if len(path.parts) != 2 or path.parts[0] != "repos":
        raise SafetyError(f"{prefix}repository path must be a direct child of repos/")
    return path.as_posix()


def parse_config(text: str) -> SafetyConfig:
    """Parse the deliberately small YAML subset used by git-safety.yaml."""
    values: dict[str, object] = {}
    own_repositories: list[str] = []
    in_own_list = False

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise SafetyError(f"line {line_number}: tabs are not allowed for indentation")

        if not raw_line.startswith(" "):
            in_own_list = False
            match = KEY_VALUE_PATTERN.fullmatch(raw_line)
            if match is None:
                raise SafetyError(f"line {line_number}: expected 'key: value'")
            key, raw_value = match.groups()
            if key not in {"schema_version", "default_class", "own_repositories"}:
                raise SafetyError(f"line {line_number}: unsupported field: {key}")
            if key in values:
                raise SafetyError(f"line {line_number}: duplicate field: {key}")

            if key == "own_repositories":
                values[key] = own_repositories
                if not raw_value.strip():
                    in_own_list = True
                elif _parse_scalar(raw_value, line_number) != "[]":
                    raise SafetyError(
                        f"line {line_number}: 'own_repositories' must be a list"
                    )
            else:
                values[key] = _parse_scalar(raw_value, line_number)
            continue

        if not in_own_list or not raw_line.startswith("  - "):
            raise SafetyError(f"line {line_number}: invalid list indentation")
        own_repositories.append(
            _validate_repository_path(_parse_scalar(raw_line[4:], line_number), line_number)
        )

    if values.get("schema_version") != "1":
        raise SafetyError("'schema_version' must be 1")
    if values.get("default_class") != "client":
        raise SafetyError("'default_class' must be client")
    if "own_repositories" not in values:
        raise SafetyError("missing 'own_repositories' field")
    if len(own_repositories) != len(set(own_repositories)):
        raise SafetyError("'own_repositories' contains duplicate paths")
    return SafetyConfig(tuple(own_repositories))


def load_config(path: Path = CONFIG_PATH) -> SafetyConfig:
    if not path.is_file():
        raise SafetyError(f"Git safety configuration not found: {path}")
    try:
        return parse_config(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise SafetyError(f"cannot read Git safety configuration: {error}") from error


def run_git(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise SafetyError(f"cannot run Git: {error}") from error


def git_output(repo: Path, *args: str) -> str | None:
    result = run_git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else None


def discover_repository_paths(workspace_root: Path = WORKSPACE_ROOT) -> list[Path]:
    root = workspace_root / "repos"
    if not root.is_dir():
        raise SafetyError(f"repository area not found: {root}")
    return sorted(
        (path for path in root.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    )


def repository_common_dir(repo: Path) -> Path:
    if repo.is_symlink():
        raise SafetyError(f"repository path must not be a symlink: {repo}")
    top_level = git_output(repo, "rev-parse", "--show-toplevel")
    if top_level is None:
        raise SafetyError(f"direct child is not a Git working tree: {repo}")
    if Path(top_level).resolve() != repo.resolve():
        raise SafetyError(f"repository must be a Git top-level working tree: {repo}")
    common = git_output(repo, "rev-parse", "--git-common-dir")
    if common is None:
        raise SafetyError(f"cannot resolve Git common directory: {repo}")
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = repo / common_path
    return common_path.resolve()


def inspect_repositories(
    workspace_root: Path = WORKSPACE_ROOT, config: SafetyConfig | None = None
) -> list[RepositoryInfo]:
    config = config or load_config(workspace_root / "_Mission-Control" / "git-safety.yaml")
    paths = discover_repository_paths(workspace_root)
    by_relative = {
        path.relative_to(workspace_root).as_posix(): path for path in paths
    }

    explicit_own_common_dirs: set[Path] = set()
    for relative_path in config.own_repositories:
        path = by_relative.get(relative_path)
        if path is None:
            raise SafetyError(
                f"own repository path is absent; remove the stale allowlist entry: {relative_path}"
            )
        explicit_own_common_dirs.add(repository_common_dir(path))

    result: list[RepositoryInfo] = []
    for relative_path, path in sorted(by_relative.items()):
        common_dir = repository_common_dir(path)
        repository_class = (
            "own"
            if relative_path in config.own_repositories
            or common_dir in explicit_own_common_dirs
            else "client"
        )
        result.append(
            RepositoryInfo(relative_path, path, common_dir, repository_class)
        )
    return result


def porcelain_entries(repo: Path) -> list[tuple[str, str]]:
    result = run_git(repo, "status", "--porcelain=v1", "-z")
    if result.returncode != 0 or not result.stdout:
        return []
    chunks = result.stdout.split("\0")
    entries: list[tuple[str, str]] = []
    index = 0
    while index < len(chunks):
        value = chunks[index]
        index += 1
        if not value:
            continue
        if len(value) < 4:
            continue
        code, path = value[:2], value[3:]
        if code[0] in {"R", "C"} and index < len(chunks):
            # In -z form the destination is in the first entry; skip the source.
            index += 1
        entries.append((code, path))
    return entries


def coordination_artifacts(entries: Iterable[tuple[str, str]]) -> list[str]:
    hits: set[str] = set()
    for _code, path in entries:
        parts = PurePosixPath(path).parts
        if not parts:
            continue
        if parts[-1] in ARTIFACT_NAMES or any(part in ARTIFACT_DIRS for part in parts):
            hits.add(path)
    return sorted(hits)


def hook_path(repo: RepositoryInfo) -> Path:
    return repo.common_dir / "hooks" / "pre-push"


def hook_state(repo: RepositoryInfo) -> str:
    custom = git_output(repo.path, "config", "--get", "core.hooksPath")
    if custom:
        return f"custom:{custom}"
    path = hook_path(repo)
    if not path.exists():
        return "missing"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return "other"
    return "installed" if HOOK_MARKER in text else "other"


def branch_summary(repo: Path) -> tuple[str, list[str]]:
    warnings: list[str] = []
    branch = git_output(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch is None:
        branch = "detached"
        warnings.append("detached HEAD")

    entries = porcelain_entries(repo)
    parts = [branch, "clean" if not entries else f"changes:{len(entries)}"]
    upstream = git_output(
        repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"
    )
    if upstream is None:
        parts.append("no-upstream")
    elif branch != "detached":
        _, separator, upstream_branch = upstream.partition("/")
        if not separator or upstream_branch != branch:
            warnings.append(f"upstream mismatch: {branch} -> {upstream}")
        counts = git_output(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        if counts:
            ahead, _, behind = counts.partition("\t")
            if ahead != "0":
                parts.append(f"ahead:{ahead}")
            if behind != "0":
                parts.append(f"behind:{behind}")
    return "  ".join(parts), warnings


def command_status(_args: argparse.Namespace) -> int:
    try:
        repositories = inspect_repositories()
    except SafetyError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    if not repositories:
        print("ยังไม่มี Git repository ใต้ repos/")

    for repo in repositories:
        summary, branch_warnings = branch_summary(repo.path)
        state = hook_state(repo)
        print(
            f"{repo.repository_class:<6} {repo.relative_path}  {summary}  hook:{state}"
        )
        for warning in branch_warnings:
            errors.append(f"{repo.relative_path}: {warning}")
        if state != "installed":
            warnings.append(
                f"{repo.relative_path}: pre-push guard is {state}; "
                "run git_guard.py install"
            )
        for artifact in coordination_artifacts(porcelain_entries(repo.path)):
            warnings.append(
                f"{repo.relative_path}: review pending coordination artifact: {artifact}"
            )

    sys.stdout.flush()
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 2 if errors else 0


def _select_repositories(
    repositories: list[RepositoryInfo], requested: list[str]
) -> list[RepositoryInfo]:
    if not requested:
        return repositories
    by_path = {repo.relative_path: repo for repo in repositories}
    selected: list[RepositoryInfo] = []
    for value in requested:
        normalized = _validate_repository_path(value)
        if normalized not in by_path:
            raise SafetyError(f"repository not found: {normalized}")
        selected.append(by_path[normalized])
    return selected


def hook_template(path: Path = HOOK_TEMPLATE_PATH) -> str:
    try:
        template = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SafetyError(f"cannot read pre-push hook template: {path}") from error
    if HOOK_MARKER not in template:
        raise SafetyError(f"invalid pre-push hook template: {path}")
    return template


def install_hook(repo: RepositoryInfo) -> str:
    template = hook_template()
    custom = git_output(repo.path, "config", "--get", "core.hooksPath")
    if custom:
        raise SafetyError(
            f"{repo.relative_path}: core.hooksPath is already set to {custom}; "
            "refusing to alter repository-owned hooks"
        )
    path = hook_path(repo)
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise SafetyError(
                f"{repo.relative_path}: cannot inspect existing pre-push hook"
            ) from error
        if HOOK_MARKER not in existing:
            raise SafetyError(
                f"{repo.relative_path}: an unrelated pre-push hook already exists; "
                "refusing to overwrite it"
            )
        if existing == template:
            return "already installed"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(template, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return "installed"


def command_install(args: argparse.Namespace) -> int:
    try:
        repositories = inspect_repositories()
        selected = _select_repositories(repositories, args.repositories)
        seen_hooks: set[Path] = set()
        for repo in selected:
            path = hook_path(repo)
            if path in seen_hooks:
                print(f"shared {repo.relative_path}  uses an already processed Git common dir")
                continue
            seen_hooks.add(path)
            result = install_hook(repo)
            print(f"{result:<17} {repo.relative_path}")
    except (OSError, SafetyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


def _is_zero_oid(value: str) -> bool:
    return bool(value) and set(value) == {"0"}


def validate_push_line(repo: Path, line: str) -> str | None:
    fields = line.split()
    if len(fields) != 4:
        return "cannot parse the refs Git intends to push"
    local_ref, local_oid, remote_ref, remote_oid = fields
    if local_ref == "(delete)" or _is_zero_oid(local_oid):
        return f"remote ref deletion is blocked: {remote_ref}"

    if local_ref == "HEAD":
        branch = git_output(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
        if branch is None:
            return "pushing from detached HEAD is blocked"
        local_ref = f"refs/heads/{branch}"

    if local_ref.startswith("refs/heads/") and remote_ref.startswith("refs/heads/"):
        if local_ref != remote_ref:
            return f"local and remote branch names must match: {local_ref} -> {remote_ref}"
        if _is_zero_oid(remote_oid):
            return None
        result = run_git(repo, "merge-base", "--is-ancestor", remote_oid, local_oid)
        if result.returncode != 0:
            return f"non-fast-forward or unverifiable branch update is blocked: {remote_ref}"
        return None

    if local_ref.startswith("refs/tags/") and remote_ref.startswith("refs/tags/"):
        if local_ref != remote_ref:
            return f"local and remote tag names must match: {local_ref} -> {remote_ref}"
        if not _is_zero_oid(remote_oid):
            return f"moving an existing remote tag is blocked: {remote_ref}"
        return None

    return f"unsupported ref update is blocked: {local_ref} -> {remote_ref}"


def command_pre_push(_args: argparse.Namespace) -> int:
    try:
        config = load_config()
        repository_root_text = git_output(Path.cwd(), "rev-parse", "--show-toplevel")
        if repository_root_text is None:
            raise SafetyError("pre-push guard is not running inside a Git working tree")
        repository_root = Path(repository_root_text).resolve()
        repositories = inspect_repositories(config=config)
        match = next(
            (repo for repo in repositories if repo.path.resolve() == repository_root), None
        )
        if match is None:
            raise SafetyError("repository is outside the guarded repos/ area")
        if match.repository_class == "client":
            raise SafetyError(
                f"all remote writes are blocked for client repository: {match.relative_path}"
            )

        errors = [
            error
            for line in sys.stdin.read().splitlines()
            if line.strip()
            if (error := validate_push_line(match.path, line)) is not None
        ]
        if errors:
            raise SafetyError("; ".join(errors))
    except SafetyError as error:
        print(f"Working Deck blocked this push: {error}", file=sys.stderr)
        print("The hook can be bypassed, so remote permissions remain the hard boundary.", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser(
        "status", help="inspect every repository and its Git safety state"
    )
    status_parser.set_defaults(handler=command_status)

    install_parser = subparsers.add_parser(
        "install", help="install the optional pre-push guard without overwriting hooks"
    )
    install_parser.add_argument(
        "repositories",
        nargs="*",
        metavar="repos/NAME",
        help="specific repository paths; omit to install for every repository",
    )
    install_parser.set_defaults(handler=command_install)

    pre_push_parser = subparsers.add_parser(
        "pre-push", help="internal entry point used by the installed Git hook"
    )
    pre_push_parser.add_argument("remote_name", nargs="?")
    pre_push_parser.add_argument("remote_url", nargs="?")
    pre_push_parser.set_defaults(handler=command_pre_push)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
