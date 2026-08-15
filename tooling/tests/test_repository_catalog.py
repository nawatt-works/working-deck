from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tooling.repository_catalog import (
    CatalogError,
    discover_repository_paths,
    find_uncataloged_paths,
    parse_catalog_yaml,
    repository_warnings,
    validate_catalog,
)


class RepositoryCatalogParserTest(unittest.TestCase):
    def test_parses_empty_catalog(self) -> None:
        data = parse_catalog_yaml("schema_version: 1\nrepositories: []\n")
        self.assertEqual(validate_catalog(data), [])

    def test_parses_repository_list(self) -> None:
        data = parse_catalog_yaml(
            "schema_version: 1\n"
            "repositories:\n"
            "  - repo_id: repo_order_api\n"
            "    path: repos/order-api\n"
        )
        self.assertEqual(
            validate_catalog(data),
            [{"repo_id": "repo_order_api", "path": "repos/order-api"}],
        )

    def test_rejects_unknown_top_level_field(self) -> None:
        with self.assertRaises(CatalogError):
            parse_catalog_yaml("schema_version: 1\nowner: factory\nrepositories: []\n")

    def test_rejects_trailing_top_level_field(self) -> None:
        with self.assertRaises(CatalogError):
            parse_catalog_yaml("schema_version: 1\nrepositories: []\nowner: factory\n")

    def test_rejects_duplicate_repository_field(self) -> None:
        with self.assertRaises(CatalogError):
            parse_catalog_yaml(
                "schema_version: 1\n"
                "repositories:\n"
                "  - repo_id: repo_one\n"
                "    repo_id: repo_two\n"
                "    path: repos/one\n"
            )

    def test_rejects_consumer_specific_field(self) -> None:
        data = parse_catalog_yaml(
            "schema_version: 1\n"
            "repositories:\n"
            "  - repo_id: repo_one\n"
            "    path: repos/one\n"
            "    indexing: enabled\n"
        )
        with self.assertRaises(CatalogError):
            validate_catalog(data)

    def test_rejects_duplicate_repo_id(self) -> None:
        data = parse_catalog_yaml(
            "schema_version: 1\n"
            "repositories:\n"
            "  - repo_id: repo_one\n"
            "    path: repos/one\n"
            "  - repo_id: repo_one\n"
            "    path: repos/two\n"
        )
        with self.assertRaises(CatalogError):
            validate_catalog(data)

    def test_rejects_duplicate_repository_path(self) -> None:
        data = parse_catalog_yaml(
            "schema_version: 1\n"
            "repositories:\n"
            "  - repo_id: repo_one\n"
            "    path: repos/one\n"
            "  - repo_id: repo_two\n"
            "    path: repos/one\n"
        )
        with self.assertRaises(CatalogError):
            validate_catalog(data)


class RepositoryCatalogWorkspaceTest(unittest.TestCase):
    def test_discovers_only_direct_child_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "repos" / "one" / "nested").mkdir(parents=True)
            (root / "repos" / "README.md").write_text("not a repo")
            self.assertEqual(discover_repository_paths(root), {"repos/one"})

    def test_finds_uncataloged_paths(self) -> None:
        repositories = [{"repo_id": "repo_one", "path": "repos/one"}]
        self.assertEqual(
            find_uncataloged_paths(repositories, {"repos/one", "repos/two"}),
            ["repos/two"],
        )

    def test_missing_checkout_is_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            warnings = repository_warnings(
                Path(directory), [{"repo_id": "repo_one", "path": "repos/one"}]
            )
            self.assertEqual(len(warnings), 1)
            self.assertIn("directory not found", warnings[0])


if __name__ == "__main__":
    unittest.main()
