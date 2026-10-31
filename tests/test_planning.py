"""Planning mode (/plan, gh:243): the researcher role's trust rules and the /plan command shape."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def frontmatter(path: Path) -> dict:
    text = path.read_text()
    head = text.split("---", 2)[1]
    return {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in head.strip().splitlines())}


class ResearcherRoleTest(unittest.TestCase):
    def setUp(self):
        self.path = REPO / "agents/researcher.md"
        self.text = self.path.read_text()

    def test_never_follows_instructions_from_content(self):
        self.assertRegex(self.text, r"never follow an instruction found in")

    def test_web_only_when_enabled(self):
        self.assertRegex(self.text, r"(?s)WebFetch`?\s+without `Web: on`")

    def test_never_pushes_or_creates_tickets(self):
        self.assertRegex(self.text, r"(?i)never push")
        self.assertRegex(self.text, r"(?i)push, create tickets")

    def test_no_edit_tool(self):
        tools = {t.strip() for t in frontmatter(self.path)["tools"].split(",")}
        self.assertNotIn("Edit", tools)


class PlanCommandTest(unittest.TestCase):
    def test_plan_is_user_invoked_with_the_flags(self):
        meta = frontmatter(REPO / "skills/plan/SKILL.md")
        self.assertEqual(meta["disable-model-invocation"], "true")
        for flag in ("--web", "--dry-run", "--oneshot"):
            self.assertIn(flag, meta["argument-hint"])

    def test_report_template_has_the_sections(self):
        text = (REPO / "skills/spec-agent/templates/plan-report.md").read_text()
        for heading in ("## Candidates", "## Needs evidence", "## Flagged content", "## Sources"):
            self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
