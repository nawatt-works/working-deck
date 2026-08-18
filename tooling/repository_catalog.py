"""Dependency-free Repository Catalog contract parser and validator."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ID_PATTERN = re.compile(r"repo_[a-z0-9]+(?:_[a-z0-9]+)*")
KEY_VALUE_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")


class CatalogError(ValueError):
    """Raised when a Repository Catalog violates the workspace contract."""


def _parse_scalar(value: str, line_number: int) -> str:
    value = value.strip()
    if not value:
        raise CatalogError(f"line {line_number}: expected a scalar value")
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise CatalogError(f"line {line_number}: invalid quoted value") from error
        if not isinstance(parsed, str):
            raise CatalogError(f"line {line_number}: expected a string")
        return parsed
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise CatalogError(f"line {line_number}: invalid quoted value")
        return value[1:-1].replace("''", "'")
    scalar = value.split(" #", 1)[0].strip()
    if not scalar:
        raise CatalogError(f"line {line_number}: expected a scalar value")
    return scalar


def _parse_key_value(value: str, line_number: int) -> tuple[str, str]:
    match = KEY_VALUE_PATTERN.fullmatch(value)
    if not match:
        raise CatalogError(f"line {line_number}: expected 'key: value'")
    key, scalar = match.groups()
    return key, scalar


def parse_catalog_yaml(text: str) -> dict[str, Any]:
    """Parse the strict YAML subset used by Repository Catalog schema version 1."""
    data: dict[str, Any] = {}
    repositories: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_repository_list = False

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise CatalogError(f"line {line_number}: tabs are not allowed for indentation")

        if not raw_line.startswith(" "):
            current = None
            in_repository_list = False
            key, raw_value = _parse_key_value(raw_line, line_number)
            if key not in {"schema_version", "repositories"}:
                raise CatalogError(f"line {line_number}: unsupported top-level field: {key}")
            if key in data:
                raise CatalogError(f"line {line_number}: duplicate top-level field: {key}")

            if key == "schema_version":
                data[key] = _parse_scalar(raw_value, line_number)
                continue

            if not raw_value.strip():
                data[key] = repositories
                in_repository_list = True
                continue
            if _parse_scalar(raw_value, line_number) == "[]":
                data[key] = repositories
                continue
            raise CatalogError(f"line {line_number}: 'repositories' must be a list")

        if not in_repository_list:
            raise CatalogError(f"line {line_number}: unexpected indented content")

        if raw_line.startswith("  - ") and not raw_line.startswith("   - "):
            current = {}
            repositories.append(current)
            item = raw_line[4:]
        elif raw_line.startswith("    ") and not raw_line.startswith("     "):
            if current is None:
                raise CatalogError(f"line {line_number}: expected a repository list item")
            item = raw_line[4:]
        else:
            raise CatalogError(f"line {line_number}: invalid repository indentation")

        key, raw_value = _parse_key_value(item, line_number)
        if key in current:
            raise CatalogError(f"line {line_number}: duplicate repository field: {key}")
        current[key] = _parse_scalar(raw_value, line_number)

    if "schema_version" not in data:
        raise CatalogError("missing top-level 'schema_version' key")
    if "repositories" not in data:
        raise CatalogError("missing top-level 'repositories' key")
    return data


def load_catalog(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise CatalogError(f"catalog not found: {path}")
    return validate_catalog(parse_catalog_yaml(path.read_text(encoding="utf-8")))


def validate_catalog(data: dict[str, Any]) -> list[dict[str, str]]:
    unexpected_top_level = set(data) - {"schema_version", "repositories"}
    if unexpected_top_level:
        unexpected = ", ".join(sorted(unexpected_top_level))
        raise CatalogError(f"unsupported top-level fields: {unexpected}")
    if data.get("schema_version") not in (1, "1"):
        raise CatalogError("'schema_version' must be 1")

    repositories = data.get("repositories")
    if not isinstance(repositories, list):
        raise CatalogError("'repositories' must be a list")

    result: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, item in enumerate(repositories, 1):
        if not isinstance(item, dict):
            raise CatalogError(f"repository #{index} must be a mapping")
        unexpected_keys = set(item) - {"repo_id", "path"}
        if unexpected_keys:
            unexpected = ", ".join(sorted(unexpected_keys))
            raise CatalogError(f"repository #{index} has unsupported fields: {unexpected}")

        repo_id = item.get("repo_id")
        path_value = item.get("path")
        if not isinstance(repo_id, str) or not REPO_ID_PATTERN.fullmatch(repo_id):
            raise CatalogError(f"repository #{index} has an invalid 'repo_id'")
        if not isinstance(path_value, str) or not path_value.strip():
            raise CatalogError(f"repository '{repo_id}' has an invalid 'path'")

        relative_path = PurePosixPath(path_value)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise CatalogError(f"repository '{repo_id}' path must be workspace-relative")
        if len(relative_path.parts) != 2 or relative_path.parts[0] != "repos":
            raise CatalogError(f"repository '{repo_id}' path must be a direct child of repos/")
        normalized_path = relative_path.as_posix()
        if repo_id in seen_ids:
            raise CatalogError(f"duplicate repo_id: {repo_id}")
        if normalized_path in seen_paths:
            raise CatalogError(f"duplicate repository path: {normalized_path}")

        seen_ids.add(repo_id)
        seen_paths.add(normalized_path)
        result.append({"repo_id": repo_id, "path": normalized_path})
    return result


def discover_repository_paths(workspace_root: Path) -> set[str]:
    repositories_root = workspace_root / "repos"
    if not repositories_root.is_dir():
        return set()
    return {
        path.relative_to(workspace_root).as_posix()
        for path in repositories_root.iterdir()
        if path.is_dir()
    }


def find_uncataloged_paths(
    repositories: list[dict[str, str]], discovered_paths: set[str]
) -> list[str]:
    cataloged_paths = {repository["path"] for repository in repositories}
    return sorted(discovered_paths - cataloged_paths)


def repository_warnings(
    workspace_root: Path, repositories: list[dict[str, str]]
) -> list[str]:
    """Return catalog-level warnings about cataloged repositories.

    รายงานเฉพาะเรื่องสมาชิกภาพของ Catalog เท่านั้น ส่วนการมีหรือไม่มี .git เป็น
    tracking mode ซึ่ง repos_status.py เป็นเจ้าของ เพราะการตัดสินว่าถูกหรือผิด
    ต้องดู opt-in ใน .gitignore ประกอบด้วย directory ที่ไม่มี .git แล้ว opt-in
    ไว้เป็น internal repository ที่ถูกต้อง ไม่ใช่ข้อยกเว้น
    """
    warnings: list[str] = []
    for repository in repositories:
        repository_path = workspace_root / repository["path"]
        if not repository_path.is_dir():
            warnings.append(f"repository directory not found: {repository_path}")
    return warnings
