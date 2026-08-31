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
    HOOK_ROOT_PLACEHOLDER,
    RepositoryRegistration,
    SafetyConfig,
    SafetyError,
    coordination_artifacts,
    discover_repository_paths,
    hook_path,
    hook_state,
    inspect_repositories,
    install_hook,
    is_ignored_by_root,
    parse_config,
    porcelain_entries,
    validate_push_line,
    validate_repository_path,
    workspace_is_git_root,
)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def init_repo(path: Path, branch: str = "main") -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", branch)
    git(path, "config", "user.name", "Working Deck Test")
    git(path, "config", "user.email", "test@example.invalid")
    (path / "README.md").write_text("test\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-q", "-m", "initial")


def registration(path: str, repository_class: str = "client") -> RepositoryRegistration:
    return RepositoryRegistration(path, repository_class)


class ConfigTest(unittest.TestCase):
    def test_empty_registry(self) -> None:
        config = parse_config(
            "schema_version: 1\ndefault_class: client\nrepositories: []\n"
        )
        self.assertEqual(config, SafetyConfig(()))

    def test_parses_grouped_and_arbitrary_paths(self) -> None:
        config = parse_config(
            "schema_version: 1\n"
            "default_class: client\n"
            "repositories:\n"
            "  - path: repos/customer-a/api\n"
            "    class: client\n"
            '  - path: "internal tools/release"\n'
            "    class: own\n"
        )
        self.assertEqual(
            config.repositories,
            (
                registration("repos/customer-a/api"),
                registration("internal tools/release", "own"),
            ),
        )

    def test_default_must_remain_client(self) -> None:
        with self.assertRaisesRegex(SafetyError, "must be client"):
            parse_config(
                "schema_version: 1\ndefault_class: own\nrepositories: []\n"
            )

    def test_entry_requires_path_and_class(self) -> None:
        with self.assertRaisesRegex(SafetyError, "exactly 'path' and 'class'"):
            parse_config(
                "schema_version: 1\n"
                "default_class: client\n"
                "repositories:\n"
                "  - path: repos/api\n"
            )

    def test_rejects_unknown_class(self) -> None:
        with self.assertRaisesRegex(SafetyError, "client or own"):
            parse_config(
                "schema_version: 1\n"
                "default_class: client\n"
                "repositories:\n"
                "  - path: repos/api\n"
                "    class: partner\n"
            )

    def test_rejects_mission_control_path(self) -> None:
        with self.assertRaisesRegex(SafetyError, "cannot live under"):
            validate_repository_path("_Mission-Control/vendor")

    def test_rejects_workspace_root_and_parent_escape(self) -> None:
        with self.assertRaisesRegex(SafetyError, "workspace root"):
            validate_repository_path(".")
        with self.assertRaisesRegex(SafetyError, "workspace-relative"):
            validate_repository_path("../customer")

    def test_rejects_duplicate_and_nested_registrations(self) -> None:
        duplicate = (
            "schema_version: 1\n"
            "default_class: client\n"
            "repositories:\n"
            "  - path: clients/api\n"
            "    class: client\n"
            "  - path: clients/api\n"
            "    class: own\n"
        )
        with self.assertRaisesRegex(SafetyError, "duplicate"):
            parse_config(duplicate)

        nested = duplicate.replace("clients/api\n    class: own", "clients/api/submodule\n    class: own")
        with self.assertRaisesRegex(SafetyError, "nested"):
            parse_config(nested)


class RepositoryInspectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "_Mission-Control").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_discovers_grouped_and_standalone_repositories(self) -> None:
        init_repo(self.root / "repos/customer-a/api")
        init_repo(self.root / "standalone")
        discovered = [
            path.relative_to(self.root).as_posix()
            for path in discover_repository_paths(self.root)
        ]
        self.assertEqual(discovered, ["repos/customer-a/api", "standalone"])

    def test_does_not_scan_mission_control(self) -> None:
        init_repo(self.root / "_Mission-Control/fixture")
        self.assertEqual(discover_repository_paths(self.root), [])

    def test_stops_at_repository_boundary(self) -> None:
        outer = self.root / "clients/app"
        init_repo(outer)
        init_repo(outer / "nested")
        discovered = [
            path.relative_to(self.root).as_posix()
            for path in discover_repository_paths(self.root)
        ]
        self.assertEqual(discovered, ["clients/app"])

    def test_registered_arbitrary_path_uses_declared_class(self) -> None:
        init_repo(self.root / "clients/acme/api")
        inspection = inspect_repositories(
            self.root, SafetyConfig((registration("clients/acme/api"),))
        )
        repo = inspection.repositories[0]
        self.assertEqual(repo.repository_class, "client")
        self.assertEqual(repo.registration, "registered")

    def test_unregistered_repository_fails_closed_as_client(self) -> None:
        init_repo(self.root / "experiments/prototype")
        inspection = inspect_repositories(self.root, SafetyConfig(()))
        repo = inspection.repositories[0]
        self.assertEqual(repo.repository_class, "client")
        self.assertEqual(repo.registration, "unregistered")

    def test_missing_registration_is_preserved_as_warning_state(self) -> None:
        expected = registration("clients/missing", "own")
        inspection = inspect_repositories(self.root, SafetyConfig((expected,)))
        self.assertEqual(inspection.repositories, ())
        self.assertEqual(inspection.missing_registrations, (expected,))

    def test_linked_worktree_inherits_registered_class(self) -> None:
        primary = self.root / "internal/tools"
        worktree = self.root / "worktrees/tools-feature"
        init_repo(primary)
        git(primary, "worktree", "add", "-q", "-b", "feature/test", str(worktree))
        inspection = inspect_repositories(
            self.root, SafetyConfig((registration("internal/tools", "own"),))
        )
        repositories = {repo.relative_path: repo for repo in inspection.repositories}
        inherited = repositories["worktrees/tools-feature"]
        self.assertEqual(inherited.repository_class, "own")
        self.assertEqual(inherited.registration, "worktree:internal/tools")

    def test_conflicting_worktree_classes_are_rejected(self) -> None:
        primary = self.root / "internal/tools"
        worktree = self.root / "worktrees/tools-feature"
        init_repo(primary)
        git(primary, "worktree", "add", "-q", "-b", "feature/test", str(worktree))
        config = SafetyConfig(
            (
                registration("internal/tools", "own"),
                registration("worktrees/tools-feature", "client"),
            )
        )
        with self.assertRaisesRegex(SafetyError, "conflicting classes"):
            inspect_repositories(self.root, config)

    def test_registered_symlink_is_rejected(self) -> None:
        outside = self.root / "outside"
        init_repo(outside)
        linked = self.root / "clients/linked"
        linked.parent.mkdir()
        os.symlink(outside, linked)
        with self.assertRaisesRegex(SafetyError, "must not be a symlink"):
            inspect_repositories(
                self.root, SafetyConfig((registration("clients/linked"),))
            )


class RootIgnoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        git(self.root, "init", "-q")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_detects_workspace_git_root(self) -> None:
        self.assertTrue(workspace_is_git_root(self.root))

    def test_checks_arbitrary_nested_repository_ignore(self) -> None:
        path = "clients/acme/api"
        (self.root / ".gitignore").write_text(f"/{path}/\n", encoding="utf-8")
        (self.root / path).mkdir(parents=True)
        self.assertTrue(is_ignored_by_root(path, self.root))
        self.assertFalse(is_ignored_by_root("clients/acme/web", self.root))


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
        self.repo_path = root / "clients/acme/api"
        init_repo(self.repo_path)
        self.info = inspect_repositories(
            root, SafetyConfig((registration("clients/acme/api"),))
        ).repositories[0]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_installs_guard_in_git_directory(self) -> None:
        self.assertEqual(install_hook(self.info), "installed")
        self.assertEqual(hook_state(self.info), "installed")
        text = hook_path(self.info).read_text(encoding="utf-8")
        self.assertIn(HOOK_MARKER, text)
        self.assertNotIn(HOOK_ROOT_PLACEHOLDER, text)
        self.assertIn(str(self.info.workspace_root.resolve()), text)
        self.assertTrue(os.access(hook_path(self.info), os.X_OK))

    def test_moved_workspace_hook_is_reported_stale(self) -> None:
        install_hook(self.info)
        path = hook_path(self.info)
        text = path.read_text(encoding="utf-8").replace(
            str(self.info.workspace_root.resolve()), "/moved/workspace"
        )
        path.write_text(text, encoding="utf-8")
        self.assertEqual(hook_state(self.info), "stale")

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

    def test_workspace_path_is_safely_shell_quoted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "deck's workspace"
            repo_path = root / "client"
            init_repo(repo_path)
            info = inspect_repositories(
                root, SafetyConfig((registration("client"),))
            ).repositories[0]
            install_hook(info)
            result = subprocess.run(
                ["sh", "-n", str(hook_path(info))],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


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
