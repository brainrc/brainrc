"""Doctor's settings-home findings (spec 206, AC14), against a temp HOME with an explicit env."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from brainrc.doctor import _home_findings, cmd_doctor

HOME_VARS = ("HOME", "BRAINRC_HOME", "AICFG_HOME", "XDG_CONFIG_HOME", "CLAUDE_CONFIG_DIR", "CODEX_HOME")


class TestHomeFindings(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name).resolve() / "home"
        self.home.mkdir()
        self.new = self.home / ".config" / "brainrc"
        self.old = self.home / ".config" / "ai-config"

    def findings(self, **env_vars):
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env["HOME"] = str(self.home)
        env.update(env_vars)
        with mock.patch.dict(os.environ, env, clear=True):
            return _home_findings()

    def test_legacy_only_fails_with_dir_and_migrate(self):
        self.old.mkdir(parents=True)
        [(level, what, fix)] = self.findings()
        self.assertEqual(level, "FAIL")
        self.assertIn("~/.config/ai-config", what)
        self.assertIn("migrate", fix)

    def test_aicfg_home_unmigrated_fails_with_working_fix(self):
        legacy = self.home / "old-home"
        legacy.mkdir()
        [(level, what, fix)] = self.findings(AICFG_HOME=str(legacy))
        self.assertEqual(level, "FAIL")
        self.assertIn("AICFG_HOME", what)
        self.assertIn("~/old-home", what)
        self.assertIn("BRAINRC_HOME=~/.config/brainrc", fix)
        self.assertIn("migrate", fix)

    def test_aicfg_home_beside_a_filled_new_home_only_warns(self):
        legacy = self.home / "old-home"
        legacy.mkdir()
        self.new.mkdir(parents=True)
        (self.new / "instructions.md").write_text("x\n")
        [(level, what, fix)] = self.findings(AICFG_HOME=str(legacy))
        self.assertEqual(level, "WARN")
        self.assertIn("unused", what)

    def test_both_dirs_warns_old_is_unused(self):
        self.old.mkdir(parents=True)
        self.new.mkdir(parents=True)
        (self.new / "instructions.md").write_text("x\n")
        [(level, what, fix)] = self.findings()
        self.assertEqual(level, "WARN")
        self.assertIn("~/.config/ai-config", what)
        self.assertIn("unused", what)
        self.assertIn("remove", fix)

    def test_old_dir_with_an_empty_new_home_points_at_migrate_not_removal(self):
        (self.old / "packs.local.toml").parent.mkdir(parents=True)
        (self.old / "packs.local.toml").write_text("# mine\n")
        target = self.home / "x"  # BRAINRC_HOME set but not created yet
        [(level, what, fix)] = self.findings(BRAINRC_HOME=str(target))
        self.assertEqual(level, "WARN")
        self.assertNotIn("unused", what)
        self.assertIn("migrate", fix)
        self.assertNotIn("rm -r", fix)

    def test_unused_old_home_fix_quotes_the_dir(self):  # #105
        legacy = self.home / "old home"
        legacy.mkdir()
        self.new.mkdir(parents=True)
        (self.new / "instructions.md").write_text("x\n")
        [(level, what, fix)] = self.findings(AICFG_HOME=str(legacy))
        self.assertEqual(level, "WARN")
        self.assertTrue(fix.endswith("then remove it: rm -r ~/'old home'"), fix)

    def test_an_old_home_holding_the_settings_home_gets_no_rm(self):  # #105 review
        self.new.mkdir(parents=True)
        (self.new / "instructions.md").write_text("x\n")
        for old, held in ((self.home / ".config", "the settings home"), (self.home, "your home directory")):
            with self.subTest(old=old.name):
                [(level, what, fix)] = self.findings(AICFG_HOME=str(old))
                self.assertEqual(level, "WARN")
                self.assertNotIn("rm", fix)
                self.assertTrue(fix.endswith(f"it holds {held}"), fix)

    def test_only_new_dir_has_no_finding(self):
        self.new.mkdir(parents=True)
        self.assertEqual(self.findings(), [])

    def test_nothing_exists_has_no_finding(self):
        self.assertEqual(self.findings(), [])

    def test_warnings_do_not_change_exit_code(self):
        self.old.mkdir(parents=True)
        self.new.mkdir(parents=True)
        (self.new / "instructions.md").write_text("x\n")
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env["HOME"] = str(self.home)
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch("brainrc.doctor.doctor_findings", return_value=_home_findings()), \
                mock.patch("builtins.print"):
            self.assertEqual(cmd_doctor(), 0)


if __name__ == "__main__":
    unittest.main()
