#!/usr/bin/env python3
"""Inspect registered workspace repositories and guard remote Git writes.

Every work repository is registered by workspace-relative path and class in
``_Mission-Control/git-safety.yaml``. Paths may live anywhere below the workspace
except Mission Control itself. Repositories discovered but not registered fail
closed as ``client`` so a forgotten registry entry never grants push permission.
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
CONFIG_PATH = WORKSPACE_ROOT / "_Mission-Control" / "git-safety.yaml"
HOOK_TEMPLATE_PATH = WORKSPACE_ROOT / "_Mission-Control" / "hooks" / "pre-push"
HOOK_MARKER = "# Working Deck Git guard"
HOOK_ROOT_PLACEHOLDER = "__WORKING_DECK_ROOT__"
RESERVED_ROOTS = frozenset({".git", "_Mission-Control"})
ARTIFACT_NAMES = frozenset(
    {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md", "GIT_POLICY.md"}
)
ARTIFACT_DIRS = frozenset({".agents", ".claude", "_Mission-Control"})
KEY_VALUE_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")
CLASS_VALUES = frozenset({"client", "own"})


class SafetyError(ValueError):
    """Raised when Git safety configuration or repository state is invalid."""


@dataclass(frozen=True)
class RepositoryRegistration:
    path: str
    repository_class: str


@dataclass(frozen=True)
class SafetyConfig:
    repositories: tuple[RepositoryRegistration, ...]


@dataclass(frozen=True)
class RepositoryInfo:
    relative_path: str
    path: Path
    workspace_root: Path
    common_dir: Path
    repository_class: str
    registration: str


@dataclass(frozen=True)
class Inspection:
    repositories: tuple[RepositoryInfo, ...]
    missing_registrations: tuple[RepositoryRegistration, ...]


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


def _parse_key_value(value: str, line_number: int) -> tuple[str, str]:
    match = KEY_VALUE_PATTERN.fullmatch(value)
    if match is None:
        raise SafetyError(f"line {line_number}: expected 'key: value'")
    return match.groups()


def validate_repository_path(value: str, line_number: int | None = None) -> str:
    prefix = f"line {line_number}: " if line_number is not None else ""
    if not value or any(character in value for character in "\r\n\t\\"):
        raise SafetyError(f"{prefix}repository path contains unsupported characters")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise SafetyError(f"{prefix}repository path must be workspace-relative")
    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise SafetyError(f"{prefix}repository path cannot be the workspace root")
    if path.parts[0] in RESERVED_ROOTS:
        raise SafetyError(
            f"{prefix}work repositories cannot live under {path.parts[0]}/"
        )
    return normalized


def _paths_overlap(first: str, second: str) -> bool:
    first_parts = PurePosixPath(first).parts
    second_parts = PurePosixPath(second).parts
    shorter = min(len(first_parts), len(second_parts))
    return first_parts[:shorter] == second_parts[:shorter]


def parse_config(text: str) -> SafetyConfig:
    """Parse the strict YAML subset used by git-safety.yaml."""
    data: dict[str, object] = {}
    repository_items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_repository_list = False

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise SafetyError(f"line {line_number}: tabs are not allowed for indentation")

        if not raw_line.startswith(" "):
            current = None
            in_repository_list = False
            key, raw_value = _parse_key_value(raw_line, line_number)
            if key not in {"schema_version", "default_class", "repositories"}:
                raise SafetyError(f"line {line_number}: unsupported field: {key}")
            if key in data:
                raise SafetyError(f"line {line_number}: duplicate field: {key}")

            if key == "repositories":
                data[key] = repository_items
                if not raw_value.strip():
                    in_repository_list = True
                elif _parse_scalar(raw_value, line_number) != "[]":
                    raise SafetyError(
                        f"line {line_number}: 'repositories' must be a list"
                    )
            else:
                data[key] = _parse_scalar(raw_value, line_number)
            continue

        if not in_repository_list:
            raise SafetyError(f"line {line_number}: unexpected indented content")
        if raw_line.startswith("  - ") and not raw_line.startswith("   - "):
            current = {}
            repository_items.append(current)
            item = raw_line[4:]
        elif raw_line.startswith("    ") and not raw_line.startswith("     "):
            if current is None:
                raise SafetyError(f"line {line_number}: expected a repository list item")
            item = raw_line[4:]
        else:
            raise SafetyError(f"line {line_number}: invalid repository indentation")

        key, raw_value = _parse_key_value(item, line_number)
        if key not in {"path", "class"}:
            raise SafetyError(f"line {line_number}: unsupported repository field: {key}")
        if key in current:
            raise SafetyError(f"line {line_number}: duplicate repository field: {key}")
        current[key] = _parse_scalar(raw_value, line_number)

    if data.get("schema_version") != "1":
        raise SafetyError("'schema_version' must be 1")
    if data.get("default_class") != "client":
        raise SafetyError("'default_class' must be client")
    if "repositories" not in data:
        raise SafetyError("missing 'repositories' field")

    registrations: list[RepositoryRegistration] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(repository_items, 1):
        if set(item) != {"path", "class"}:
            raise SafetyError(
                f"repository #{index} must contain exactly 'path' and 'class'"
            )
        path = validate_repository_path(item["path"])
        repository_class = item["class"]
        if repository_class not in CLASS_VALUES:
            raise SafetyError(
                f"repository '{path}' class must be client or own"
            )
        if path in seen_paths:
            raise SafetyError(f"duplicate repository path: {path}")
        for existing in seen_paths:
            if _paths_overlap(path, existing):
                raise SafetyError(
                    f"nested repository registrations are not supported: "
                    f"{existing} and {path}"
                )
        seen_paths.add(path)
        registrations.append(RepositoryRegistration(path, repository_class))
    return SafetyConfig(tuple(registrations))


def load_config(path: Path = CONFIG_PATH) -> SafetyConfig:
    if not path.is_file():
        raise SafetyError(f"Git safety configuration not found: {path}")
    try:
        return parse_config(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise SafetyError(f"cannot read Git safety configuration: {error}") from error


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise SafetyError(f"cannot run Git: {error}") from error


def git_output(repo: Path, *args: str) -> str | None:
    result = run_git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else None


def _has_git_marker(path: Path) -> bool:
    try:
        return (path / ".git").exists()
    except OSError:
        return False


def discover_repository_paths(workspace_root: Path = WORKSPACE_ROOT) -> list[Path]:
    """Find Git working trees recursively, stopping at each repository boundary."""
    if not workspace_root.is_dir():
        raise SafetyError(f"workspace root not found: {workspace_root}")

    repositories: list[Path] = []
    stack: list[Path] = []
    try:
        children = sorted(workspace_root.iterdir(), key=lambda path: path.name, reverse=True)
    except OSError as error:
        raise SafetyError(f"cannot inspect workspace root: {error}") from error

    for child in children:
        if child.name not in RESERVED_ROOTS and child.is_dir():
            stack.append(child)

    while stack:
        path = stack.pop()
        if _has_git_marker(path):
            repositories.append(path)
            continue
        if path.is_symlink():
            continue
        try:
            children = sorted(path.iterdir(), key=lambda child: child.name, reverse=True)
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                stack.append(child)
    return sorted(repositories, key=lambda path: path.relative_to(workspace_root).as_posix())


def repository_common_dir(repo: Path) -> Path:
    if repo.is_symlink():
        raise SafetyError(f"repository path must not be a symlink: {repo}")
    top_level = git_output(repo, "rev-parse", "--show-toplevel")
    if top_level is None:
        raise SafetyError(f"registered path is not a Git working tree: {repo}")
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
) -> Inspection:
    config = config or load_config(workspace_root / "_Mission-Control" / "git-safety.yaml")
    discovered_paths = discover_repository_paths(workspace_root)
    discovered = {
        path.relative_to(workspace_root).as_posix(): path for path in discovered_paths
    }
    information: dict[str, RepositoryInfo] = {}
    missing: list[RepositoryRegistration] = []
    registered_common_dirs: dict[Path, RepositoryRegistration] = {}

    for registration in config.repositories:
        path = workspace_root / registration.path
        if not path.exists():
            missing.append(registration)
            continue
        if not path.is_dir():
            raise SafetyError(f"registered repository path is not a directory: {registration.path}")
        common_dir = repository_common_dir(path)
        existing = registered_common_dirs.get(common_dir)
        if existing is not None and existing.repository_class != registration.repository_class:
            raise SafetyError(
                "linked worktrees sharing one Git common directory have conflicting "
                f"classes: {existing.path} and {registration.path}"
            )
        registered_common_dirs[common_dir] = registration
        information[registration.path] = RepositoryInfo(
            registration.path,
            path,
            workspace_root,
            common_dir,
            registration.repository_class,
            "registered",
        )

    for relative_path, path in discovered.items():
        if relative_path in information:
            continue
        common_dir = repository_common_dir(path)
        inherited = registered_common_dirs.get(common_dir)
        if inherited is not None:
            repository_class = inherited.repository_class
            registration_state = f"worktree:{inherited.path}"
        else:
            repository_class = "client"
            registration_state = "unregistered"
        information[relative_path] = RepositoryInfo(
            relative_path,
            path,
            workspace_root,
            common_dir,
            repository_class,
            registration_state,
        )

    # A registered path with an invalid .git marker is not returned by discovery,
    # but it was still validated above. Registrations are therefore authoritative.
    return Inspection(
        tuple(information[path] for path in sorted(information)),
        tuple(missing),
    )


def workspace_is_git_root(workspace_root: Path = WORKSPACE_ROOT) -> bool:
    top_level = git_output(workspace_root, "rev-parse", "--show-toplevel")
    return top_level is not None and Path(top_level).resolve() == workspace_root.resolve()


def is_ignored_by_root(relative_path: str, workspace_root: Path = WORKSPACE_ROOT) -> bool:
    result = run_git(
        workspace_root,
        "check-ignore",
        "-q",
        "--no-index",
        "--",
        relative_path,
    )
    return result.returncode == 0


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
        if not value or len(value) < 4:
            continue
        code, path = value[:2], value[3:]
        if code[0] in {"R", "C"} and index < len(chunks):
            index += 1  # -z puts the rename/copy source in the following field.
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
    if HOOK_MARKER not in text:
        return "other"
    return "installed" if text == render_hook(repo) else "stale"


def branch_summary(repo: Path) -> tuple[str, list[str]]:
    errors: list[str] = []
    branch = git_output(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch is None:
        branch = "detached"
        errors.append("detached HEAD")

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
            errors.append(f"upstream mismatch: {branch} -> {upstream}")
        counts = git_output(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        if counts:
            ahead, _, behind = counts.partition("\t")
            if ahead != "0":
                parts.append(f"ahead:{ahead}")
            if behind != "0":
                parts.append(f"behind:{behind}")
    return "  ".join(parts), errors


def command_status(_args: argparse.Namespace) -> int:
    try:
        inspection = inspect_repositories()
    except SafetyError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    root_is_git = workspace_is_git_root()
    if not root_is_git:
        warnings.append(
            "workspace root is not a Git root; nested-repository ignore safety cannot be checked"
        )

    if not inspection.repositories and not inspection.missing_registrations:
        print("ยังไม่มี Git repository ที่ลงทะเบียนหรือค้นพบใน workspace")

    for repo in inspection.repositories:
        summary, branch_errors = branch_summary(repo.path)
        state = hook_state(repo)
        print(
            f"{repo.repository_class:<6} {repo.registration:<24} "
            f"{repo.relative_path}  {summary}  hook:{state}"
        )
        if repo.registration == "unregistered":
            errors.append(
                f"{repo.relative_path}: unregistered repository; treated as client"
            )
        for error in branch_errors:
            errors.append(f"{repo.relative_path}: {error}")
        if root_is_git and not is_ignored_by_root(repo.relative_path):
            errors.append(
                f"{repo.relative_path}: root Git does not ignore this repository; "
                "adding it may create a gitlink"
            )
        if state != "installed":
            warnings.append(
                f"{repo.relative_path}: pre-push guard is {state}; "
                "run git_guard.py install"
            )
        for artifact in coordination_artifacts(porcelain_entries(repo.path)):
            warnings.append(
                f"{repo.relative_path}: review pending coordination artifact: {artifact}"
            )

    for registration in inspection.missing_registrations:
        warnings.append(
            f"{registration.path}: registered as {registration.repository_class} "
            "but checkout is not present"
        )

    sys.stdout.flush()
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 2 if errors else 0


def _select_repositories(
    repositories: tuple[RepositoryInfo, ...], requested: list[str]
) -> list[RepositoryInfo]:
    if not requested:
        return list(repositories)
    by_path = {repo.relative_path: repo for repo in repositories}
    selected: list[RepositoryInfo] = []
    for value in requested:
        normalized = validate_repository_path(value)
        if normalized not in by_path:
            raise SafetyError(f"repository checkout not found: {normalized}")
        selected.append(by_path[normalized])
    return selected


def hook_template(path: Path = HOOK_TEMPLATE_PATH) -> str:
    try:
        template = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SafetyError(f"cannot read pre-push hook template: {path}") from error
    if HOOK_MARKER not in template or HOOK_ROOT_PLACEHOLDER not in template:
        raise SafetyError(f"invalid pre-push hook template: {path}")
    return template


def _shell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def render_hook(repo: RepositoryInfo) -> str:
    root = _shell_single_quote(str(repo.workspace_root.resolve()))
    return hook_template().replace(HOOK_ROOT_PLACEHOLDER, root)


def install_hook(repo: RepositoryInfo) -> str:
    template = render_hook(repo)
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
        inspection = inspect_repositories()
        selected = _select_repositories(inspection.repositories, args.repositories)
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
        inspection = inspect_repositories(config=config)
        match = next(
            (
                repo
                for repo in inspection.repositories
                if repo.path.resolve() == repository_root
            ),
            None,
        )
        if match is None:
            raise SafetyError("repository is outside this Working Deck workspace")
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
        print(
            "The hook can be bypassed, so remote permissions remain the hard boundary.",
            file=sys.stderr,
        )
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser(
        "status", help="inspect registered and discovered workspace repositories"
    )
    status_parser.set_defaults(handler=command_status)

    install_parser = subparsers.add_parser(
        "install", help="install the optional pre-push guard without overwriting hooks"
    )
    install_parser.add_argument(
        "repositories",
        nargs="*",
        metavar="PATH",
        help="specific workspace-relative paths; omit to install for every checkout",
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
