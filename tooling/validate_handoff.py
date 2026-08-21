#!/usr/bin/env python3
"""Validate handoff documents against the workspace handoff contract."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from .handoff import count_work_items, validate_handoff
    from .repository_catalog import CatalogError, load_catalog
except ImportError:
    from handoff import count_work_items, validate_handoff  # type: ignore[no-redef]
    from repository_catalog import CatalogError, load_catalog  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "workbench" / "handoff"
CATALOG = ROOT / "workbench" / "repositories.yaml"


def main() -> int:
    if not HANDOFF.is_dir():
        print(f"ok: no handoff area at {HANDOFF}")
        return 0

    try:
        repositories = load_catalog(CATALOG)
        known_repo_ids = {repository["repo_id"] for repository in repositories}
        errors = validate_handoff(HANDOFF, known_repo_ids)
        work_items = count_work_items(HANDOFF)
    except (CatalogError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 2

    print(f"ok: {HANDOFF} ({work_items} work items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
