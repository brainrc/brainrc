"""docs/roadmap.md is the epic list (#203): one well-formed line per epic, each linking its issue."""
import re
import unittest
from pathlib import Path

ROADMAP = Path(__file__).resolve().parent.parent / "docs/roadmap.md"
EPIC = re.compile(r"^- \*\*(?P<id>[A-Z]\d+)\*\* \[[^\]]+\]\(https://github\.com/brainrc/brainrc/issues/(?P<n>\d+)\)(?::\s+\S.*)?$")


class RoadmapTest(unittest.TestCase):
    def setUp(self):
        self.lines = ROADMAP.read_text().splitlines()
        self.items = [line for line in self.lines if line.startswith("- ")]

    def test_every_item_is_an_epic_with_its_issue_link(self):
        bad = [line for line in self.items if not EPIC.match(line)]
        self.assertEqual(bad, [], "each roadmap item: - **<ID>** [title](https://github.com/brainrc/brainrc/issues/N): goal")

    def test_ids_and_issues_are_unique(self):
        found = [EPIC.match(line) for line in self.items]
        ids = [m["id"] for m in found if m]
        issues = [m["n"] for m in found if m]
        self.assertEqual(len(ids), len(set(ids)), ids)
        self.assertEqual(len(issues), len(set(issues)), issues)

    def test_items_are_grouped_under_waves(self):
        first_item = next(i for i, line in enumerate(self.lines) if line.startswith("- "))
        self.assertTrue(any(line.startswith("## Wave 0") for line in self.lines[:first_item]))

    def test_points_to_the_changelog_for_shipped_work(self):
        self.assertIn("[CHANGELOG](../CHANGELOG.md)", ROADMAP.read_text())


if __name__ == "__main__":
    unittest.main()
