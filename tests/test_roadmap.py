"""docs/roadmap.md is the epic list (#203), grouped by release gate (#300): one line per epic."""
import re
import unittest
from pathlib import Path

ROADMAP = Path(__file__).resolve().parent.parent / "docs/roadmap.md"
# An epic sits under a gate heading (one per GitHub milestone) or the waiting-to-close group.
GATES = ("Gate A: public launch", "Gate B: v1.0", "Gate C: team adoption")
GROUP = re.compile(r"^(Gate [A-C]: .+|Open, with every sub-issue closed)$")
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

    def test_every_item_is_under_a_wave_or_group_heading(self):
        heading, misplaced = None, []
        for line in self.lines:
            if line.startswith("## "):
                heading = line[3:]
            elif line.startswith("- ") and not (heading and GROUP.match(heading)):
                misplaced.append(f"{heading}: {line}")
        self.assertEqual(misplaced, [], "roadmap items belong under a gate or group heading")

    def test_gates_appear_in_order(self):
        headings = [line[3:] for line in self.lines if line.startswith("## ")]
        self.assertEqual([h for h in headings if h.startswith("Gate ")], list(GATES))

    def test_names_every_epic_from_e26_to_e33(self):
        # Each is either an open epic's line or named among the gate's shipped epics.
        listed = {m["id"] for m in map(EPIC.match, self.items) if m}
        shipped = " ".join(line for line in self.lines if line.startswith("Shipped in this gate:"))
        missing = [f"E{n}" for n in range(26, 34) if f"E{n}" not in listed and not re.search(rf"\bE{n}\b", shipped)]
        self.assertEqual(missing, [], "docs/roadmap.md must name E26 to E33")

    def test_points_to_the_changelog_for_shipped_work(self):
        self.assertIn("[CHANGELOG](../CHANGELOG.md)", ROADMAP.read_text())


if __name__ == "__main__":
    unittest.main()
