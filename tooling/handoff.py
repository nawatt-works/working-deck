"""Dependency-free Handoff contract parser and validator.

`workspace-meta/handoff/` เป็นพื้นที่ที่สิทธิ์เขียนกำหนดด้วย stage
แทนตำแหน่ง artifact ปกติของ producer เอกสารจึงต้องบอกได้ด้วยตัวเองว่าเป็นของหน่วยงานใด
stage ใด และพร้อมให้ producer ตัวถัดไปลงมือทำตามหรือยัง โมดูลนี้ตรวจข้อตกลง
เหล่านั้นตาม contract ที่ workspace-meta/contracts/handoff/
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path


WORK_ID_PATTERN = re.compile(r"(\d{8})-[a-z0-9]+(?:-[a-z0-9]+)*")
STAGE_FILE_PATTERN = re.compile(r"(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md")
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REPO_ID_PATTERN = re.compile(r"repo_[a-z0-9]+(?:_[a-z0-9]+)*")
KEY_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")

FENCE = "---"
STATUS_VALUES = ("draft", "ready", "superseded")
REQUIRED_FIELDS = ("work_id", "stage", "status", "author")
OPTIONAL_FIELDS = ("repos",)
LIST_FIELDS = frozenset({"repos"})


class HandoffError(ValueError):
    """Raised when a handoff document cannot be parsed at all."""


def _parse_scalar(value: str, line_number: int) -> str:
    value = value.strip()
    if not value:
        raise HandoffError(f"line {line_number}: expected a scalar value")
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise HandoffError(f"line {line_number}: invalid quoted value") from error
        if not isinstance(parsed, str):
            raise HandoffError(f"line {line_number}: expected a string")
        return parsed
    if value.startswith("'"):
        if not value.endswith("'") or len(value) < 2:
            raise HandoffError(f"line {line_number}: invalid quoted value")
        return value[1:-1].replace("''", "'")
    scalar = value.split(" #", 1)[0].strip()
    if not scalar:
        raise HandoffError(f"line {line_number}: expected a scalar value")
    return scalar


def _parse_inline_list(value: str, line_number: int) -> list[str]:
    if not value.endswith("]"):
        raise HandoffError(f"line {line_number}: unterminated inline list")
    body = value[1:-1].strip()
    if not body:
        return []
    return [_parse_scalar(item, line_number) for item in body.split(",")]


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parse the strict YAML subset used by handoff stage frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        raise HandoffError("missing frontmatter block; the file must start with '---'")

    data: dict[str, object] = {}
    current_list_key: str | None = None

    for line_number, raw_line in enumerate(lines[1:], 2):
        stripped = raw_line.strip()
        if stripped == FENCE:
            return data
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- "):
            if current_list_key is None:
                raise HandoffError(f"line {line_number}: list item outside of a field")
            values = data[current_list_key]
            assert isinstance(values, list)
            values.append(_parse_scalar(stripped[2:], line_number))
            continue

        key, separator, raw_value = stripped.partition(":")
        key = key.strip()
        if not separator or not KEY_PATTERN.fullmatch(key):
            raise HandoffError(f"line {line_number}: expected 'key: value'")
        if key in data:
            raise HandoffError(f"line {line_number}: duplicate field: {key}")

        value = raw_value.strip()
        if value.startswith("["):
            data[key] = _parse_inline_list(value, line_number)
            current_list_key = None
        elif not value:
            data[key] = []
            current_list_key = key
        else:
            data[key] = _parse_scalar(value, line_number)
            current_list_key = None

    raise HandoffError("frontmatter block is not closed with '---'")


def document_errors(
    work_id: str,
    stage_from_file_name: str,
    data: dict[str, object],
    known_repo_ids: set[str],
) -> list[str]:
    """Return every contract violation found in one stage document."""
    errors: list[str] = []

    unexpected = set(data) - set(REQUIRED_FIELDS) - set(OPTIONAL_FIELDS)
    if unexpected:
        fields = ", ".join(sorted(unexpected))
        errors.append(f"unsupported frontmatter fields: {fields}")
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing required frontmatter field: {field}")

    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if field in data and not isinstance(value, str):
            errors.append(f"'{field}' must be a single value")

    declared_work_id = data.get("work_id")
    if isinstance(declared_work_id, str) and declared_work_id != work_id:
        errors.append(
            f"'work_id' is {declared_work_id} but the work item directory is {work_id}"
        )

    declared_stage = data.get("stage")
    if isinstance(declared_stage, str) and declared_stage != stage_from_file_name:
        errors.append(
            f"'stage' is {declared_stage} but the file name says {stage_from_file_name}"
        )

    status = data.get("status")
    if isinstance(status, str) and status not in STATUS_VALUES:
        allowed = ", ".join(STATUS_VALUES)
        errors.append(f"'status' is {status}; allowed values are {allowed}")

    author = data.get("author")
    if isinstance(author, str) and not SLUG_PATTERN.fullmatch(author):
        errors.append(f"'author' must be kebab-case: {author}")

    repos = data.get("repos")
    if "repos" in data:
        if not isinstance(repos, list):
            errors.append("'repos' must be a list of repo_id values")
        else:
            for repo_id in repos:
                if not REPO_ID_PATTERN.fullmatch(repo_id):
                    errors.append(f"'repos' contains an invalid repo_id: {repo_id}")
                elif repo_id not in known_repo_ids:
                    errors.append(f"'repos' names a repo_id absent from the catalog: {repo_id}")

    return errors


def _work_id_errors(work_id: str) -> list[str]:
    if not WORK_ID_PATTERN.fullmatch(work_id):
        return ["invalid work_id; expected YYYYMMDD-<kebab-slug>"]
    stamp = work_id[:8]
    try:
        date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8]))
    except ValueError:
        return [f"work_id must start with a real calendar date: {stamp}"]
    return []


def work_item_errors(directory: Path, known_repo_ids: set[str]) -> list[str]:
    """Return every contract violation found in one work item directory."""
    work_id = directory.name
    label = f"handoff/{work_id}"
    errors = [f"{label}: {message}" for message in _work_id_errors(work_id)]

    stage_files: list[tuple[Path, str, str]] = []
    for child in sorted(directory.iterdir()):
        if child.name.startswith(".") or child.is_dir():
            continue
        match = STAGE_FILE_PATTERN.fullmatch(child.name)
        if match is None:
            errors.append(
                f"{label}/{child.name}: unexpected file; "
                f"stage files are named <NN>-<stage>.md"
            )
            continue
        order, stage = match.groups()
        stage_files.append((child, order, stage))

    if not stage_files:
        errors.append(f"{label}: work item has no stage file")

    seen_orders: dict[str, str] = {}
    seen_stages: dict[str, str] = {}
    for path, order, stage in stage_files:
        if order in seen_orders:
            errors.append(
                f"{label}/{path.name}: order {order} is already used by {seen_orders[order]}"
            )
        if stage in seen_stages:
            errors.append(
                f"{label}/{path.name}: stage '{stage}' is already used by {seen_stages[stage]}"
            )
        seen_orders.setdefault(order, path.name)
        seen_stages.setdefault(stage, path.name)

        try:
            data = parse_frontmatter(path.read_text(encoding="utf-8"))
        except HandoffError as error:
            errors.append(f"{label}/{path.name}: {error}")
            continue
        errors.extend(
            f"{label}/{path.name}: {message}"
            for message in document_errors(work_id, stage, data, known_repo_ids)
        )

    return errors


def validate_handoff(handoff_root: Path, known_repo_ids: set[str]) -> list[str]:
    """Return every contract violation found in the whole handoff area."""
    errors: list[str] = []
    for entry in sorted(handoff_root.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_file():
            if entry.name != "README.md":
                errors.append(
                    f"handoff/{entry.name}: unexpected file at the handoff root; "
                    f"every work item is a directory"
                )
            continue
        if entry.is_dir():
            errors.extend(work_item_errors(entry, known_repo_ids))
    return errors


def count_work_items(handoff_root: Path) -> int:
    return sum(
        1
        for entry in handoff_root.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )
