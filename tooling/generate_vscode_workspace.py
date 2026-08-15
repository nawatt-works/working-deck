#!/usr/bin/env python3
"""Generate the committed VS Code multi-root workspace from the Repository Catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / ".workbench" / "repositories.yaml"
DEFAULT_OUTPUT = ROOT / ".code-workspace"


class ManifestError(ValueError):
    """Raised when the Repository Catalog is invalid."""


def _scalar(value: str, line_number: int) -> str:
    value = value.strip()
    if not value:
        raise ManifestError(f"line {line_number}: expected a scalar value")
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise ManifestError(f"line {line_number}: invalid quoted value") from error
        if not isinstance(parsed, str):
            raise ManifestError(f"line {line_number}: expected a string")
        return parsed
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise ManifestError(f"line {line_number}: invalid quoted value")
        return value[1:-1].replace("''", "'")
    return value.split(" #", 1)[0].strip()


def _load_minimal_yaml(path: Path) -> dict[str, Any]:
    """Read the intentionally small Repository Catalog schema without dependencies."""
    repositories: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_repositories = False
    schema_version: str | None = None
    key_value = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        if not in_repositories:
            if stripped.startswith("schema_version:"):
                schema_version = _scalar(stripped.split(":", 1)[1], line_number)
                continue
            if stripped == "repositories: []":
                in_repositories = True
                continue
            if stripped == "repositories:":
                in_repositories = True
            continue
        if not raw_line.startswith((" ", "\t")):
            break

        if stripped.startswith("- "):
            current = {}
            repositories.append(current)
            item = stripped[2:].strip()
        else:
            if current is None:
                raise ManifestError(f"line {line_number}: expected a repository list item")
            item = stripped

        match = key_value.match(item)
        if not match:
            raise ManifestError(f"line {line_number}: expected 'key: value'")
        key, value = match.groups()
        current[key] = _scalar(value, line_number)

    if not in_repositories:
        raise ManifestError("missing top-level 'repositories' key")
    return {"schema_version": schema_version, "repositories": repositories}


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f"manifest not found: {path}")
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return _load_minimal_yaml(path)

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ManifestError("catalog root must be a mapping")
    return data


def validate_repositories(data: dict[str, Any]) -> list[dict[str, str]]:
    unexpected_top_level = set(data) - {"schema_version", "repositories"}
    if unexpected_top_level:
        unexpected = ", ".join(sorted(unexpected_top_level))
        raise ManifestError(f"unsupported top-level fields: {unexpected}")

    schema_version = data.get("schema_version")
    if schema_version not in (1, "1"):
        raise ManifestError("'schema_version' must be 1")

    repositories = data.get("repositories")
    if not isinstance(repositories, list):
        raise ManifestError("'repositories' must be a list")

    result: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, item in enumerate(repositories, 1):
        if not isinstance(item, dict):
            raise ManifestError(f"repository #{index} must be a mapping")
        unexpected_keys = set(item) - {"repo_id", "path"}
        if unexpected_keys:
            unexpected = ", ".join(sorted(unexpected_keys))
            raise ManifestError(f"repository #{index} has unsupported fields: {unexpected}")
        repo_id = item.get("repo_id")
        path_value = item.get("path")
        if not isinstance(repo_id, str) or not repo_id.strip():
            raise ManifestError(f"repository #{index} has an invalid 'repo_id'")
        if not re.fullmatch(r"repo_[a-z0-9]+(?:_[a-z0-9]+)*", repo_id):
            raise ManifestError(f"repo_id must match repo_<snake_case_name>: {repo_id}")
        if not isinstance(path_value, str) or not path_value.strip():
            raise ManifestError(f"repository '{repo_id}' has an invalid 'path'")

        relative_path = PurePosixPath(path_value)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ManifestError(f"repository '{repo_id}' path must be workspace-relative")
        if len(relative_path.parts) != 2 or relative_path.parts[0] != "repos":
            raise ManifestError(f"repository '{repo_id}' path must be a direct child of repos/")
        normalized_path = relative_path.as_posix()
        if repo_id in seen_ids:
            raise ManifestError(f"duplicate repo_id: {repo_id}")
        if normalized_path in seen_paths:
            raise ManifestError(f"duplicate repository path: {normalized_path}")
        seen_ids.add(repo_id)
        seen_paths.add(normalized_path)
        result.append({"repo_id": repo_id, "path": normalized_path})
    return result


def render_workspace(repositories: list[dict[str, str]]) -> str:
    workspace = {
        "folders": [
            {"name": "workspace", "path": "."},
            *(
                {
                    "name": PurePosixPath(repository["path"]).name,
                    "path": repository["path"],
                }
                for repository in repositories
            ),
        ],
        "settings": {
            "files.exclude": {"repos": True},
            "search.exclude": {"repos/**": True},
        },
    }
    return json.dumps(workspace, ensure_ascii=False, indent=2) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the output is stale")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repositories = validate_repositories(load_manifest(DEFAULT_MANIFEST))
        expected = render_workspace(repositories)
    except (ManifestError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    for repository in repositories:
        repository_path = ROOT / repository["path"]
        if not repository_path.is_dir():
            print(f"warning: repository directory not found: {repository_path}", file=sys.stderr)
        elif not (repository_path / ".git").exists():
            print(f"warning: cataloged path is not a Git checkout: {repository_path}", file=sys.stderr)

    output = DEFAULT_OUTPUT
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != expected:
            print(f"stale: {output}", file=sys.stderr)
            return 1
        print(f"ok: {output}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8")
    print(f"generated: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
