#!/usr/bin/env python3
"""Validate the Repository Catalog contract and workspace membership."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from .repository_catalog import (
        CatalogError,
        discover_repository_paths,
        find_uncataloged_paths,
        load_catalog,
        repository_warnings,
    )
except ImportError:
    from repository_catalog import (  # type: ignore[no-redef]
        CatalogError,
        discover_repository_paths,
        find_uncataloged_paths,
        load_catalog,
        repository_warnings,
    )


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "workspace-meta" / "repositories.yaml"


def main() -> int:
    try:
        repositories = load_catalog(CATALOG)
        uncataloged_paths = find_uncataloged_paths(
            repositories, discover_repository_paths(ROOT)
        )
        if uncataloged_paths:
            paths = ", ".join(uncataloged_paths)
            raise CatalogError(
                f"workspace repository directories missing from catalog: {paths}"
            )
    except (CatalogError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    for warning in repository_warnings(ROOT, repositories):
        print(f"warning: {warning}", file=sys.stderr)
    print(f"ok: {CATALOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
