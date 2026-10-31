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


class TicketGateTest(unittest.TestCase):
    def setUp(self):
        text = (REPO / "skills/spec-agent/references/planning.md").read_text()
        self.gate = text.split("## Ticket gate", 1)[1]

    def test_gate_lists_each_ticket_as_an_outward_action(self):
        self.assertRegex(self.gate, r"(?i)outward action")
        self.assertRegex(self.gate, r"(?i)nothing\s+is\s+created\s+until")

    def test_gate_is_recorded_like_other_gates(self):
        self.assertIn("gates.ticket", self.gate)
        self.assertIn("metrics.gates.ticket", self.gate)

    def test_dry_run_creates_nothing(self):
        self.assertRegex(self.gate, r"(?i)`--dry-run`[^.]*never call[s]? `create`")

    def test_cap_and_deferred(self):
        self.assertRegex(self.gate, r"(?i)at most 10")
        self.assertRegex(self.gate, r"(?i)deferred")

    def test_oneshot_creates_local_tickets_only(self):
        self.assertRegex(self.gate, r"`--oneshot`")
        self.assertIn("github create refused", self.gate)

    def test_guardrails_names_the_ticket_gate(self):
        text = (REPO / "skills/spec-agent/references/guardrails.md").read_text()
        self.assertRegex(text, r"Gate reached \(Spec, Plan, Deliver, Ticket\)")


if __name__ == "__main__":
    unittest.main()
