from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tooling.handoff import (
    HandoffError,
    document_errors,
    parse_frontmatter,
    validate_handoff,
    work_item_errors,
)


READY_PLAN = """---
work_id: 20260821-order-refund-flow
stage: plan
status: ready
author: planner
repos: [repo_api]
---

# Plan
"""


def write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


class ParseFrontmatterTest(unittest.TestCase):
    def test_parses_scalars_and_an_inline_list(self) -> None:
        data = parse_frontmatter(READY_PLAN)
        self.assertEqual(data["work_id"], "20260821-order-refund-flow")
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["repos"], ["repo_api"])

    def test_parses_a_block_list(self) -> None:
        text = "---\nstage: plan\nrepos:\n  - repo_api\n  - repo_web\n---\n"
        self.assertEqual(parse_frontmatter(text)["repos"], ["repo_api", "repo_web"])

    def test_skips_comments_and_blank_lines(self) -> None:
        text = "---\n# note\n\nstage: plan\n---\n"
        self.assertEqual(parse_frontmatter(text), {"stage": "plan"})

    def test_rejects_a_file_without_a_frontmatter_block(self) -> None:
        with self.assertRaises(HandoffError):
            parse_frontmatter("# Plan\n\nstage: plan\n")

    def test_rejects_an_unclosed_frontmatter_block(self) -> None:
        with self.assertRaises(HandoffError):
            parse_frontmatter("---\nstage: plan\n")

    def test_rejects_a_duplicate_field(self) -> None:
        with self.assertRaises(HandoffError):
            parse_frontmatter("---\nstage: plan\nstage: audit\n---\n")

    def test_rejects_a_list_item_outside_a_field(self) -> None:
        with self.assertRaises(HandoffError):
            parse_frontmatter("---\n- repo_api\n---\n")


class DocumentErrorsTest(unittest.TestCase):
    def data(self, **overrides: object) -> dict[str, object]:
        data: dict[str, object] = {
            "work_id": "20260821-order-refund-flow",
            "stage": "plan",
            "status": "ready",
            "author": "planner",
        }
        data.update(overrides)
        return data

    def test_accepts_a_document_that_matches_its_location(self) -> None:
        errors = document_errors(
            "20260821-order-refund-flow", "plan", self.data(), set()
        )
        self.assertEqual(errors, [])

    def test_flags_a_work_id_that_disagrees_with_the_directory(self) -> None:
        errors = document_errors(
            "20260821-other-work", "plan", self.data(), set()
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("work_id", errors[0])

    def test_flags_a_stage_that_disagrees_with_the_file_name(self) -> None:
        errors = document_errors(
            "20260821-order-refund-flow", "audit", self.data(), set()
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("stage", errors[0])

    def test_flags_an_unknown_status(self) -> None:
        errors = document_errors(
            "20260821-order-refund-flow", "plan", self.data(status="done"), set()
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("status", errors[0])

    def test_flags_a_missing_required_field(self) -> None:
        data = self.data()
        del data["author"]
        errors = document_errors("20260821-order-refund-flow", "plan", data, set())
        self.assertEqual(errors, ["missing required frontmatter field: author"])

    def test_flags_a_field_the_contract_does_not_define(self) -> None:
        errors = document_errors(
            "20260821-order-refund-flow", "plan", self.data(owner="planner"), set()
        )
        self.assertEqual(errors, ["unsupported frontmatter fields: owner"])

    def test_flags_a_repo_id_that_is_not_in_the_catalog(self) -> None:
        errors = document_errors(
            "20260821-order-refund-flow",
            "plan",
            self.data(repos=["repo_api"]),
            {"repo_web"},
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("absent from the catalog", errors[0])

    def test_accepts_a_repo_id_that_is_in_the_catalog(self) -> None:
        errors = document_errors(
            "20260821-order-refund-flow",
            "plan",
            self.data(repos=["repo_api"]),
            {"repo_api"},
        )
        self.assertEqual(errors, [])


class WorkItemErrorsTest(unittest.TestCase):
    def test_accepts_a_well_formed_work_item(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "20260821-order-refund-flow"
            work_item.mkdir()
            write(work_item, "10-plan.md", READY_PLAN)
            self.assertEqual(work_item_errors(work_item, {"repo_api"}), [])

    def test_ignores_attachment_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "20260821-order-refund-flow"
            work_item.mkdir()
            write(work_item, "10-plan.md", READY_PLAN)
            (work_item / "evidence").mkdir()
            write(work_item / "evidence", "trace.log", "noise\n")
            self.assertEqual(work_item_errors(work_item, {"repo_api"}), [])

    def test_flags_an_empty_work_item(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "20260821-order-refund-flow"
            work_item.mkdir()
            errors = work_item_errors(work_item, set())
            self.assertEqual(len(errors), 1)
            self.assertIn("no stage file", errors[0])

    def test_flags_a_work_id_that_is_not_a_real_date(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "20260231-order-refund-flow"
            work_item.mkdir()
            write(work_item, "10-plan.md", READY_PLAN)
            errors = work_item_errors(work_item, {"repo_api"})
            self.assertTrue(any("real calendar date" in error for error in errors))

    def test_flags_a_work_id_without_a_date_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "order-refund-flow"
            work_item.mkdir()
            write(work_item, "10-plan.md", READY_PLAN)
            errors = work_item_errors(work_item, {"repo_api"})
            self.assertTrue(any("invalid work_id" in error for error in errors))

    def test_flags_a_file_that_is_not_a_stage_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "20260821-order-refund-flow"
            work_item.mkdir()
            write(work_item, "10-plan.md", READY_PLAN)
            write(work_item, "notes.md", "scratch\n")
            errors = work_item_errors(work_item, {"repo_api"})
            self.assertEqual(len(errors), 1)
            self.assertIn("<NN>-<stage>.md", errors[0])

    def test_flags_two_stage_files_sharing_one_order(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "20260821-order-refund-flow"
            work_item.mkdir()
            write(work_item, "10-plan.md", READY_PLAN)
            write(work_item, "10-audit.md", READY_PLAN.replace("plan", "audit"))
            errors = work_item_errors(work_item, {"repo_api"})
            self.assertTrue(any("already used by" in error for error in errors))

    def test_reports_a_document_that_cannot_be_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            work_item = Path(raw) / "20260821-order-refund-flow"
            work_item.mkdir()
            write(work_item, "10-plan.md", "# Plan without frontmatter\n")
            errors = work_item_errors(work_item, set())
            self.assertEqual(len(errors), 1)
            self.assertIn("missing frontmatter block", errors[0])


class ValidateHandoffTest(unittest.TestCase):
    def test_allows_the_area_readme_but_not_other_root_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            handoff = Path(raw)
            write(handoff, "README.md", "# Handoff\n")
            write(handoff, "plan.md", "stray\n")
            errors = validate_handoff(handoff, set())
            self.assertEqual(len(errors), 1)
            self.assertIn("handoff/plan.md", errors[0])

    def test_accepts_an_area_with_only_its_readme(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            handoff = Path(raw)
            write(handoff, "README.md", "# Handoff\n")
            self.assertEqual(validate_handoff(handoff, set()), [])


if __name__ == "__main__":
    unittest.main()
