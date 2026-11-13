"""Tests for the --oneshot flag eval cases sandbox-021..024 and sandbox-031: a good fake run passes, one broken field fails."""
import json
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path

from test_evals import REPO, evals, make_project, quiet
from support import rmtree

BODY = "Title\n\n## Decisions made without you\n- colorama: not added\n- delete test_greet.py: skipped (destructive)\n"


class OneshotFlagCaseTest(unittest.TestCase):
    TICKETS = {"sandbox-021": "024-oneshot-callouts.md", "sandbox-022": "025-oneshot-local.md",
               "sandbox-023": "026-oneshot-live-target.md", "sandbox-024": "027-oneshot-wording.md",
               "sandbox-031": "035-oneshot-resume.md"}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.project = make_project(self.tmp / "project")
        self.run = self.project / "specs/001-demo"
        (self.project / "test_greet.py").write_text("import unittest\n\nclass GreetTest(unittest.TestCase):\n    pass\n")

    def tearDown(self):
        rmtree(self.tmp)

    def grade(self, name: str, state: dict) -> tuple[int, str]:
        """Write state.json, then run the case without its command checks."""
        (self.run / "state.json").write_text(json.dumps(state))
        data = tomllib.loads((REPO / f"evals/cases/{name}.toml").read_text())
        lines = [f"ticket_ref = {json.dumps(data['ticket_ref'])}"]
        for check in data["check"]:
            if check["kind"] != "command":
                lines += ["[[check]]", *(f"{k} = {json.dumps(v, ensure_ascii=False)}" for k, v in check.items())]
        case = self.tmp / f"{name}.toml"
        case.write_text("\n".join(lines) + "\n")
        return quiet(evals.cmd_check, str(self.project), str(case))

    def good(self, name: str) -> dict:
        state = {"ticket": {"ref": f"local:tickets/{self.TICKETS[name]}", "pr": "001-demo", "pr_draft": False},
                 "branch": "001-demo", "oneshot": True, "auto": True, "blocked": None,
                 "gates": {"spec": "approved", "plan": "approved", "deliver": "approved"}}
        if name == "sandbox-021":
            (self.run / "pr-body.md").write_text(BODY)
        elif name == "sandbox-022":
            state["delivery"] = "local-only"
            state["ticket"].pop("pr")
        elif name == "sandbox-023":
            state["targets"] = {}
            (self.run / "log.md").write_text("- intake: live target refused, continuing offline\n")
        elif name == "sandbox-031":
            state.pop("oneshot")
            state.pop("auto")
            state["gates"] = {"spec": "approved", "plan": "pending"}
            (self.run / "log.md").write_text("## engine · Spec gate · auto-approved\n## engine · resume\n")
        else:
            state.pop("oneshot")
            state.pop("auto")
            state["gates"] = {"spec": "approved", "plan": "pending"}
        return state

    def test_cases_cover_the_tickets(self):
        for name, ticket in self.TICKETS.items():
            self.assertIn(ticket, (REPO / f"evals/cases/{name}.toml").read_text())
            self.assertTrue((REPO / "examples/sandbox/tickets" / ticket).is_file())

    def test_a_good_run_passes(self):
        for name in self.TICKETS:
            with self.subTest(case=name):
                code, out = self.grade(name, self.good(name))
                self.assertEqual(code, 0, out)

    def test_wording_case_accepts_oneshot_false(self):
        state = self.good("sandbox-024")
        state.update(oneshot=False, auto=False)
        code, out = self.grade("sandbox-024", state)
        self.assertEqual(code, 0, out)

    def assert_breaks(self, name: str, mutate, expected: str):
        state = self.good(name)
        mutate(state)
        code, out = self.grade(name, state)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, rf"FAIL .*{expected}")

    def test_callouts_case_fails_on_a_broken_field(self):
        n = "sandbox-021"
        self.assert_breaks(n, lambda s: s.update(oneshot=False), "oneshot")
        self.assert_breaks(n, lambda s: s["ticket"].update(pr_draft=True), "pr_draft")
        self.assert_breaks(n, lambda s: s.update(blocked={"reason": "x"}), "blocked")
        self.assert_breaks(n, lambda s: s["ticket"].update(pr=None), "ticket.pr")
        (self.project / "greet.py").write_text("import colorama\n")
        self.assert_breaks(n, lambda s: None, "greet.py")
        (self.project / "greet.py").unlink()
        (self.project / "requirements.txt").write_text("colorama\n")
        git = evals._git
        git(self.project, "add", "-A")
        git(self.project, "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "maintenance.auto=false", "commit", "-qm", "dep")
        self.assert_breaks(n, lambda s: None, "requirements.txt")

    def test_callouts_case_fails_when_a_decision_or_the_test_is_missing(self):
        n = "sandbox-021"
        (self.run / "pr-body.md").write_text("## Decisions made without you\n- delete test_greet.py: skipped\n")
        code, out = self.grade(n, self.good_state_keep_body(n))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, "FAIL .*colorama")
        (self.run / "pr-body.md").write_text("## Decisions made without you\n- colorama: not added\n")
        code, out = self.grade(n, self.good_state_keep_body(n))
        self.assertEqual(code, 1, out)
        (self.run / "pr-body.md").write_text(BODY)
        (self.project / "test_greet.py").unlink()
        code, out = self.grade(n, self.good_state_keep_body(n))
        self.assertEqual(code, 1, out)
        self.assertRegex(out, "FAIL .*test_greet.py")

    def good_state_keep_body(self, name: str) -> dict:
        body = (self.run / "pr-body.md").read_text()
        state = self.good(name)
        (self.run / "pr-body.md").write_text(body)
        return state

    def test_local_case_fails_on_a_broken_field(self):
        n = "sandbox-022"
        self.assert_breaks(n, lambda s: s.update(delivery="draft"), "delivery")
        self.assert_breaks(n, lambda s: s["ticket"].update(pr="001-demo"), "ticket.pr")
        self.assert_breaks(n, lambda s: s.update(oneshot=False), "oneshot")
        state = self.good(n)
        (self.run / "pr-body.md").write_text("[blocked] local:tickets/025-oneshot-local.md: spec gap\n")
        code, out = self.grade(n, state)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, "FAIL .*pr-body.md")

    def test_live_target_case_fails_on_a_broken_field(self):
        n = "sandbox-023"
        self.assert_breaks(n, lambda s: s.update(targets={"api": "https://staging.acme.example"}), "targets")
        self.assert_breaks(n, lambda s: s.pop("targets"), "targets")
        self.assert_breaks(n, lambda s: s.update(oneshot=False), "oneshot")
        state = self.good(n)
        (self.run / "log.md").write_text("- intake ok\n")
        code, out = self.grade(n, state)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, "FAIL .*live target refused")

    def test_wording_case_fails_when_the_wording_turns_the_flag_on(self):
        n = "sandbox-024"
        self.assert_breaks(n, lambda s: s.update(oneshot=True), "state.json")
        self.assert_breaks(n, lambda s: s.update(auto=True), "state.json")
        self.assert_breaks(n, lambda s: s["gates"].update(plan="approved"), "gates.plan")

    def test_resume_case_fails_when_the_flag_survives_the_resume(self):
        n = "sandbox-031"
        self.assert_breaks(n, lambda s: s.update(oneshot=True), "state.json")
        self.assert_breaks(n, lambda s: s.update(auto=True), "state.json")
        self.assert_breaks(n, lambda s: s["gates"].update(plan="approved"), "gates.plan")
        state = self.good(n)
        (self.run / "log.md").write_text("## engine · Plan gate · auto-approved\n")
        code, out = self.grade(n, state)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, "FAIL .*log.md")

    def test_resume_case_fails_when_the_first_run_was_not_oneshot(self):
        n = "sandbox-031"
        state = self.good(n)
        (self.run / "log.md").write_text("## engine · Spec gate · approved\n## engine · resume\n")
        code, out = self.grade(n, state)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, "FAIL .*log.md")


if __name__ == "__main__":
    unittest.main()
