from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLING))

from git_guard import (  # noqa: E402
    HOOK_MARKER,
    SafetyConfig,
    SafetyError,
    coordination_artifacts,
    hook_path,
    hook_state,
    inspect_repositories,
    install_hook,
    parse_config,
    porcelain_entries,
    validate_push_line,
)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    git(path, "config", "user.name", "Working Deck Test")
    git(path, "config", "user.email", "test@example.invalid")
    (path / "README.md").write_text("test\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-q", "-m", "initial")


class ConfigTest(unittest.TestCase):
    def test_empty_own_allowlist(self) -> None:
        config = parse_config(
            "schema_version: 1\ndefault_class: client\nown_repositories: []\n"
        )
        self.assertEqual(config, SafetyConfig(()))

    def test_parses_quoted_and_plain_paths(self) -> None:
        config = parse_config(
            "schema_version: 1\n"
            "default_class: client\n"
            "own_repositories:\n"
            "  - repos/tools\n"
            '  - "repos/my app"\n'
        )
        self.assertEqual(
            config.own_repositories, ("repos/tools", "repos/my app")
        )

    def test_default_must_remain_client(self) -> None:
        with self.assertRaisesRegex(SafetyError, "must be client"):
            parse_config(
                "schema_version: 1\ndefault_class: own\nown_repositories: []\n"
            )

    def test_rejects_paths_outside_repos(self) -> None:
        with self.assertRaisesRegex(SafetyError, "workspace-relative"):
            parse_config(
                "schema_version: 1\n"
                "default_class: client\n"
                "own_repositories:\n"
                "  - ../customer\n"
            )

    def test_rejects_duplicate_paths(self) -> None:
        with self.assertRaisesRegex(SafetyError, "duplicate"):
            parse_config(
                "schema_version: 1\n"
                "default_class: client\n"
                "own_repositories:\n"
                "  - repos/tools\n"
                "  - repos/tools\n"
            )


class RepositoryInspectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "repos").mkdir()
        (self.root / "_Mission-Control").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_unlisted_repository_defaults_to_client(self) -> None:
        init_repo(self.root / "repos/customer")
        repositories = inspect_repositories(self.root, SafetyConfig(()))
        self.assertEqual(repositories[0].repository_class, "client")

    def test_hidden_repository_is_not_skipped(self) -> None:
        init_repo(self.root / "repos/.customer")
        repositories = inspect_repositories(self.root, SafetyConfig(()))
        self.assertEqual(repositories[0].relative_path, "repos/.customer")
        self.assertEqual(repositories[0].repository_class, "client")

    def test_explicit_repository_is_own(self) -> None:
        init_repo(self.root / "repos/tools")
        repositories = inspect_repositories(
            self.root, SafetyConfig(("repos/tools",))
        )
        self.assertEqual(repositories[0].repository_class, "own")

    def test_linked_worktree_inherits_own_class(self) -> None:
        primary = self.root / "repos/tools"
        worktree = self.root / "repos/tools-feature"
        init_repo(primary)
        git(primary, "worktree", "add", "-q", "-b", "feature/test", str(worktree))
        repositories = inspect_repositories(
            self.root, SafetyConfig(("repos/tools",))
        )
        classes = {repo.relative_path: repo.repository_class for repo in repositories}
        self.assertEqual(classes["repos/tools-feature"], "own")

    def test_stale_own_entry_is_an_error(self) -> None:
        with self.assertRaisesRegex(SafetyError, "stale allowlist"):
            inspect_repositories(self.root, SafetyConfig(("repos/missing",)))

    def test_plain_directory_is_an_error(self) -> None:
        (self.root / "repos/not-git").mkdir()
        with self.assertRaisesRegex(SafetyError, "not a Git working tree"):
            inspect_repositories(self.root, SafetyConfig(()))

    def test_symlink_is_an_error(self) -> None:
        outside = self.root / "outside"
        init_repo(outside)
        os.symlink(outside, self.root / "repos/linked")
        with self.assertRaisesRegex(SafetyError, "must not be a symlink"):
            inspect_repositories(self.root, SafetyConfig(()))


class ArtifactTest(unittest.TestCase):
    def test_finds_coordination_artifacts(self) -> None:
        entries = [
            ("??", "AGENTS.md"),
            ("A ", ".claude/settings.json"),
            (" M", "src/app.py"),
        ]
        self.assertEqual(
            coordination_artifacts(entries), [".claude/settings.json", "AGENTS.md"]
        )

    def test_porcelain_handles_spaces_without_quote_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            init_repo(repo)
            (repo / "file with spaces.txt").write_text("x", encoding="utf-8")
            self.assertIn(("??", "file with spaces.txt"), porcelain_entries(repo))


class HookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.repo_path = root / "repos/customer"
        init_repo(self.repo_path)
        self.info = inspect_repositories(root, SafetyConfig(()))[0]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_installs_guard_in_git_directory(self) -> None:
        self.assertEqual(install_hook(self.info), "installed")
        self.assertEqual(hook_state(self.info), "installed")
        self.assertIn(HOOK_MARKER, hook_path(self.info).read_text(encoding="utf-8"))
        self.assertTrue(os.access(hook_path(self.info), os.X_OK))

    def test_install_is_idempotent(self) -> None:
        install_hook(self.info)
        self.assertEqual(install_hook(self.info), "already installed")

    def test_refuses_to_replace_existing_hook(self) -> None:
        path = hook_path(self.info)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        with self.assertRaisesRegex(SafetyError, "refusing to overwrite"):
            install_hook(self.info)

    def test_refuses_custom_hooks_path(self) -> None:
        git(self.repo_path, "config", "core.hooksPath", ".hooks")
        with self.assertRaisesRegex(SafetyError, "core.hooksPath"):
            install_hook(self.info)


class PushValidationTest(unittest.TestCase):
    ZERO = "0" * 40
    A = "a" * 40
    B = "b" * 40

    def test_allows_new_same_named_branch(self) -> None:
        line = f"refs/heads/feature/x {self.A} refs/heads/feature/x {self.ZERO}"
        with tempfile.TemporaryDirectory() as temporary:
            self.assertIsNone(validate_push_line(Path(temporary), line))

    def test_allows_head_to_same_named_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            init_repo(repo)
            branch = git(repo, "symbolic-ref", "--short", "HEAD")
            line = f"HEAD {self.A} refs/heads/{branch} {self.ZERO}"
            self.assertIsNone(validate_push_line(repo, line))

    def test_blocks_branch_name_mismatch(self) -> None:
        line = f"refs/heads/feature/x {self.A} refs/heads/main {self.ZERO}"
        with tempfile.TemporaryDirectory() as temporary:
            error = validate_push_line(Path(temporary), line)
        self.assertIn("must match", error or "")

    def test_blocks_remote_deletion(self) -> None:
        line = f"(delete) {self.ZERO} refs/heads/main {self.A}"
        with tempfile.TemporaryDirectory() as temporary:
            error = validate_push_line(Path(temporary), line)
        self.assertIn("deletion", error or "")

    def test_allows_fast_forward_and_blocks_reverse(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            init_repo(repo)
            first = git(repo, "rev-parse", "HEAD")
            (repo / "README.md").write_text("next\n", encoding="utf-8")
            git(repo, "commit", "-q", "-am", "next")
            second = git(repo, "rev-parse", "HEAD")
            forward = f"refs/heads/main {second} refs/heads/main {first}"
            reverse = f"refs/heads/main {first} refs/heads/main {second}"
            self.assertIsNone(validate_push_line(repo, forward))
            self.assertIn("non-fast-forward", validate_push_line(repo, reverse) or "")

    def test_allows_new_tag_but_blocks_moving_tag(self) -> None:
        new = f"refs/tags/v1 {self.A} refs/tags/v1 {self.ZERO}"
        move = f"refs/tags/v1 {self.A} refs/tags/v1 {self.B}"
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            self.assertIsNone(validate_push_line(repo, new))
            self.assertIn("moving", validate_push_line(repo, move) or "")


if __name__ == "__main__":
    unittest.main()
