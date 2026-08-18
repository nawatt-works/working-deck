from __future__ import annotations

import unittest

from tooling.repos_status import (
    STATE_GITLINK,
    STATE_OK_EXTERNAL,
    STATE_OK_INTERNAL,
    STATE_UNTRACKED,
    artifact_hits,
    classify,
)


class ClassifyTest(unittest.TestCase):
    def test_external_repository_keeps_its_own_git_and_stays_ignored(self) -> None:
        self.assertEqual(classify(True, True), STATE_OK_EXTERNAL)

    def test_internal_directory_has_no_git_and_is_tracked_by_root(self) -> None:
        self.assertEqual(classify(False, False), STATE_OK_INTERNAL)

    def test_own_git_without_root_ignore_would_become_a_gitlink(self) -> None:
        self.assertEqual(classify(True, False), STATE_GITLINK)

    def test_no_git_and_root_ignore_means_the_work_is_tracked_nowhere(self) -> None:
        self.assertEqual(classify(False, True), STATE_UNTRACKED)


class ArtifactHitsTest(unittest.TestCase):
    def test_flags_instruction_files_at_any_depth(self) -> None:
        entries = [("??", "AGENTS.md"), (" M", "packages/api/CLAUDE.md")]
        self.assertEqual(
            artifact_hits(entries), ["AGENTS.md", "packages/api/CLAUDE.md"]
        )

    def test_flags_coordination_directories(self) -> None:
        entries = [("??", ".claude/settings.json"), ("A ", "workbench/plan.md")]
        self.assertEqual(
            artifact_hits(entries), [".claude/settings.json", "workbench/plan.md"]
        )

    def test_ignores_ordinary_source_changes(self) -> None:
        entries = [("M ", "src/order.ts"), ("??", "docs/readme-agents.md")]
        self.assertEqual(artifact_hits(entries), [])

    def test_does_not_match_on_substrings_of_directory_names(self) -> None:
        entries = [("??", "src/workbenches/tool.ts"), ("??", "src/claude.ts")]
        self.assertEqual(artifact_hits(entries), [])

    def test_deduplicates_and_sorts(self) -> None:
        entries = [("??", "AGENTS.md"), ("A ", "AGENTS.md"), ("??", ".agents/x.yaml")]
        self.assertEqual(artifact_hits(entries), [".agents/x.yaml", "AGENTS.md"])


if __name__ == "__main__":
    unittest.main()
