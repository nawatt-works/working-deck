#!/usr/bin/env python3
"""Generate the committed VS Code multi-root workspace from the Repository Catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

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
DEFAULT_CATALOG = ROOT / "workbench" / "repositories.yaml"
DEFAULT_OUTPUT = ROOT / ".code-workspace"


def render_workspace(repositories: list[dict[str, str]]) -> str:
    workspace = {
        "folders": [
            {"name": ROOT.name, "path": "."},
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
        repositories = load_catalog(DEFAULT_CATALOG)
        uncataloged_paths = find_uncataloged_paths(
            repositories, discover_repository_paths(ROOT)
        )
        if uncataloged_paths:
            paths = ", ".join(uncataloged_paths)
            raise CatalogError(
                f"workspace repository directories missing from catalog: {paths}"
            )
        expected = render_workspace(repositories)
    except (CatalogError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    for warning in repository_warnings(ROOT, repositories):
        print(f"warning: {warning}", file=sys.stderr)

    if args.check:
        if not DEFAULT_OUTPUT.is_file() or DEFAULT_OUTPUT.read_text(encoding="utf-8") != expected:
            print(f"stale: {DEFAULT_OUTPUT}", file=sys.stderr)
            return 1
        print(f"ok: {DEFAULT_OUTPUT}")
        return 0

    DEFAULT_OUTPUT.write_text(expected, encoding="utf-8")
    print(f"generated: {DEFAULT_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
