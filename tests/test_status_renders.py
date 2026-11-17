"""`status` shows a rendered file apply would rewrite, so an edited rule isn't "in sync" (doctor's check)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, install_harnesses, quiet  # noqa: E402
from support import home_env, restore_home, rmtree, saved_home  # noqa: E402


class StatusRendersTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        self.rendered = brainrc.config.rendered_instructions()
        self.rule = sorted((self.repo / "rules").glob("*.md"))[0]

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        super().tearDown()

    def test_status_flags_an_edited_rule_until_apply(self):
        self.assertEqual(quiet(brainrc.cmd_sync, True)[0], 0)
        self.assertIn("Everything in sync.", quiet(brainrc.cmd_sync, False)[1])
        self.rule.write_text(self.rule.read_text() + "\n- An extra line the user added.\n")

        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertNotIn("Everything in sync.", out)
        self.assertIn(f"UPDATE{' ' * 14}{brainrc.config.tilde(self.rendered)}  (rules or packs changed", out)
        self.assertIn("Dry run.", out)
        stale = [f for f in brainrc.doctor_findings() if "is stale" in f[1]]
        self.assertEqual(len(stale), 1, stale)  # the same file, found the same way

        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn("An extra line the user added.", self.rendered.read_text())
        self.assertIn("Everything in sync.", quiet(brainrc.cmd_sync, False)[1])

    def test_status_writes_nothing(self):
        quiet(brainrc.cmd_sync, True)
        before = self.rendered.read_text()
        self.rule.write_text(self.rule.read_text() + "\n- Edited.\n")
        quiet(brainrc.cmd_sync, False)
        self.assertEqual(self.rendered.read_text(), before)

    def test_status_before_the_first_apply_lists_the_render(self):
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertIn(f"CREATE{' ' * 14}{brainrc.config.tilde(self.rendered)}\n", out)
        self.assertFalse(self.rendered.exists())

    def test_a_hand_edited_render_is_flagged_too(self):
        quiet(brainrc.cmd_sync, True)
        self.rendered.write_text("edited by hand\n")
        out = quiet(brainrc.cmd_sync, False)[1]
        self.assertIn("(rules or packs changed since the last apply)", out)


if __name__ == "__main__":
    unittest.main()
