"""Contract tests for the settings home: resolution order and the refusal while an old home is unmigrated
(specs 206 and 238).

Every case runs `scripts/brainrc.py` as a subprocess against a fresh temp HOME with an explicit env.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
from test_brainrc import default_pack_env  # noqa: E402
from support import home_env
HOME_VARS = ("HOME", "USERPROFILE", "BRAINRC_HOME", "AICFG_HOME", "XDG_CONFIG_HOME", "CLAUDE_CONFIG_DIR", "CODEX_HOME", "PYTHONWARNINGS")


class HomeCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.new = self.home / ".config" / "brainrc"
        self.old = self.home / ".config" / "ai-config"

    def run_cli(self, *args, home=None, **env_vars):
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env.update(default_pack_env())  # the default pack comes from a local stand-in, not GitHub
        env.update(home_env(home or self.home))
        env.update(env_vars)
        return subprocess.run(
            [sys.executable, "scripts/brainrc.py", *args], cwd=REPO, env=env,
            capture_output=True, text=True, timeout=120,
        )

    def ok(self, *args, **kw):
        proc = self.run_cli(*args, **kw)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def snapshot(self):
        return sorted(str(p.relative_to(self.tmp)) for p in self.tmp.rglob("*"))

    def refused(self, cmd, *needles, **env_vars):
        """cmd exits 1, writes nothing, and prints one ERROR line holding every needle."""
        before = self.snapshot()
        proc = self.run_cli(cmd, **env_vars)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.snapshot(), before)
        errors = [l for l in proc.stdout.splitlines() if l.startswith("ERROR")]
        self.assertEqual(len(errors), 1, proc.stdout)
        for needle in needles:
            self.assertIn(needle, errors[0])
        return proc


class TestDefaultHome(HomeCase):
    def test_ac1_apply_renders_under_config_brainrc_and_does_not_create_ai_config(self):
        proc = self.ok("apply")
        self.assertTrue((self.new / "instructions.md").is_file())
        self.assertFalse(self.old.exists())
        self.assertEqual(proc.stderr, "")


class TestEnvOverrides(HomeCase):
    def test_ac2_brainrc_home_wins_over_aicfg_home(self):
        x, y = self.tmp / "x", self.tmp / "y"
        self.ok("apply", BRAINRC_HOME=str(x), AICFG_HOME=str(y))
        self.assertTrue((x / "instructions.md").is_file())
        self.assertFalse(y.exists())
        self.assertFalse(self.new.exists())
        self.assertFalse(self.old.exists())

    def test_ac2_brainrc_home_used_even_when_legacy_dir_exists_and_does_not_warn(self):
        self.old.mkdir(parents=True)
        x = self.tmp / "x"
        proc = self.ok("apply", BRAINRC_HOME=str(x))
        self.assertTrue((x / "instructions.md").is_file())
        self.assertFalse((self.old / "instructions.md").exists())
        self.assertEqual(proc.stderr, "")


class TestXdgConfigHome(HomeCase):
    def test_ac3_absolute_xdg_uses_xdg_brainrc(self):
        xdg = self.tmp / "xdg"
        proc = self.ok("apply", XDG_CONFIG_HOME=str(xdg))
        self.assertTrue((xdg / "brainrc" / "instructions.md").is_file())
        self.assertFalse(self.new.exists())
        self.assertFalse(self.old.exists())
        self.assertEqual(proc.stderr, "")

    def test_ac4_absolute_xdg_with_only_legacy_dir_is_refused(self):
        self.old.mkdir(parents=True)
        xdg = self.tmp / "xdg"
        self.refused("apply", "ai-config", "brainrc migrate", XDG_CONFIG_HOME=str(xdg))
        self.assertFalse((xdg / "brainrc").exists())

    def test_ac3_absolute_xdg_home_present_beats_legacy_dir_without_warning(self):
        self.old.mkdir(parents=True)
        xdg = self.tmp / "xdg"
        (xdg / "brainrc").mkdir(parents=True)
        proc = self.ok("apply", XDG_CONFIG_HOME=str(xdg))
        self.assertTrue((xdg / "brainrc" / "instructions.md").is_file())
        self.assertFalse((self.old / "instructions.md").exists())
        self.assertEqual(proc.stderr, "")

    def test_ac3_empty_xdg_falls_back_to_default(self):
        self.ok("apply", XDG_CONFIG_HOME="")
        self.assertTrue((self.new / "instructions.md").is_file())

    def test_ac3_relative_xdg_falls_back_to_default(self):
        rel = "xdg-rel-206"
        self.ok("apply", XDG_CONFIG_HOME=rel)
        self.assertTrue((self.new / "instructions.md").is_file())
        self.assertFalse((REPO / rel).exists())
        self.assertFalse((self.home / rel).exists())

    def test_ac3_brainrc_home_beats_xdg(self):
        x, xdg = self.tmp / "x", self.tmp / "xdg"
        self.ok("apply", BRAINRC_HOME=str(x), XDG_CONFIG_HOME=str(xdg))
        self.assertTrue((x / "instructions.md").is_file())
        self.assertFalse(xdg.exists())


class TestLegacyHome(HomeCase):
    def test_ac4_status_apply_and_update_refuse_and_write_nothing(self):
        self.old.mkdir(parents=True)
        (self.old / "packs.local.toml").write_text("")
        for cmd in ("status", "apply", "update"):
            with self.subTest(cmd=cmd):
                proc = self.refused(cmd, "~/.config/ai-config", "brainrc migrate")
                self.assertEqual(proc.stderr, "")
        self.assertFalse(self.new.exists())

    def test_ac4_an_existing_new_home_makes_the_old_dir_ignored(self):
        self.new.mkdir(parents=True)
        self.old.mkdir(parents=True)
        (self.old / "packs.local.toml").write_text("this is [not valid toml\n")
        for cmd in ("apply", "status"):
            self.assertEqual(self.ok(cmd).stderr, "", cmd)

    def test_ac5_migrate_then_apply_succeeds(self):
        self.old.mkdir(parents=True)
        (self.old / "packs.local.toml").write_text("")
        self.ok("migrate")
        self.assertFalse(self.old.exists())
        self.assertTrue((self.new / "packs.local.toml").is_file())
        self.ok("apply")
        self.ok("status")

    def test_ac5_other_commands_do_not_refuse(self):
        self.old.mkdir(parents=True)
        for args in (("validate",), ("plugin",), ("--version",), ("migrate", "--dry-run")):
            with self.subTest(args=args):
                proc = self.run_cli(*args)
                self.assertNotIn("no longer read", proc.stdout + proc.stderr)
        proc = self.run_cli("doctor")
        fail = [line for line in proc.stdout.splitlines() if line.startswith("FAIL") and "no longer read" in line]
        self.assertEqual(len(fail), 1, proc.stdout)
        fix = proc.stdout.split(fail[0], 1)[1].lstrip("\n").splitlines()[0]
        self.assertIn("fix:", fix)
        self.assertIn("migrate", fix)


class TestAicfgHomeEnv(HomeCase):
    def message(self):
        return "ERROR AICFG_HOME is no longer read: set BRAINRC_HOME=~/.config/brainrc and run brainrc migrate"

    def test_ac3_status_apply_and_update_refuse_with_the_exact_error(self):
        y = self.tmp / "y"
        y.mkdir()
        (y / "packs.local.toml").write_text("")
        for cmd in ("status", "apply", "update"):
            with self.subTest(cmd=cmd):
                proc = self.refused(cmd, AICFG_HOME=str(y))
                self.assertEqual(proc.stdout.splitlines()[0], self.message())
        self.assertFalse(self.new.exists())

    def test_ac3_an_empty_new_home_still_refuses_but_a_filled_one_does_not(self):
        y = self.tmp / "y"
        self.new.mkdir(parents=True)
        self.refused("status", "AICFG_HOME is no longer read", AICFG_HOME=str(y))
        (self.new / "packs.local.toml").write_text("")
        self.ok("apply", AICFG_HOME=str(y))
        self.assertFalse(y.exists())

    def test_ac3_brainrc_home_set_means_aicfg_home_is_ignored(self):
        y = self.tmp / "y"
        self.assertEqual(self.ok("apply", AICFG_HOME=str(y), BRAINRC_HOME=str(self.tmp / "x")).stderr, "")
        self.assertFalse(y.exists())

    def test_ac5_migrate_with_brainrc_home_then_apply_succeeds(self):
        y, x = self.tmp / "y", self.tmp / "x"
        y.mkdir()
        (y / "packs.local.toml").write_text("")
        self.ok("migrate", AICFG_HOME=str(y), BRAINRC_HOME=str(x))
        self.assertTrue((x / "packs.local.toml").is_file())
        self.ok("apply", BRAINRC_HOME=str(x))

    def test_ac5_doctor_fails_with_the_migrate_fix(self):
        proc = self.run_cli("doctor", AICFG_HOME=str(self.tmp / "y"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("AICFG_HOME", proc.stdout)
        self.assertIn("migrate", proc.stdout)

    def test_ac5_version_validate_and_plugin_do_not_refuse(self):
        for args in (("--version",), ("validate",), ("plugin",)):
            proc = self.run_cli(*args, AICFG_HOME=str(self.tmp / "y"))
            self.assertNotIn("no longer read", proc.stdout + proc.stderr, args)
        self.assertEqual(self.run_cli("--version", AICFG_HOME=str(self.tmp / "y")).stderr, "")


class TestBothHomesExist(HomeCase):
    def test_ac6_new_dir_is_used_old_is_never_read_and_nothing_warns(self):
        self.new.mkdir(parents=True)
        self.old.mkdir(parents=True)
        # An unparseable file would make any command that reads the old home fail.
        (self.old / "packs.local.toml").write_text("this is [not valid toml\n")
        for cmd in ("apply", "status"):
            proc = self.ok(cmd)
            self.assertEqual(proc.stderr, "", cmd)
        self.assertTrue((self.new / "instructions.md").is_file())
        self.assertEqual(sorted(p.name for p in self.old.iterdir()), ["packs.local.toml"])


class HomeFunctionsTest(unittest.TestCase):
    """new_home() and former_homes() in-process, for the callers that list old homes (doctor, migrate)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.old = self.home / ".config" / "ai-config"
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env.update(default_pack_env())  # the default pack comes from a local stand-in, not GitHub
        env.update(home_env(self.home))
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.path.insert(0, str(REPO))
        self.addCleanup(sys.path.remove, str(REPO))
        from brainrc import config
        self.config = config

    def test_new_home_ignores_aicfg_home_and_legacy(self):
        self.old.mkdir(parents=True)
        os.environ["AICFG_HOME"] = str(self.tmp / "y")
        self.assertEqual(self.config.new_home(), self.home / ".config" / "brainrc")

    def test_former_homes_lists_aicfg_home_and_legacy_when_brainrc_home_is_set(self):
        os.environ["BRAINRC_HOME"] = str(self.tmp / "x")
        os.environ["AICFG_HOME"] = str(self.tmp / "y")
        self.assertEqual(self.config.former_homes(), [self.tmp / "y", self.old])

    def test_brainrc_home_at_the_legacy_path_is_not_a_former_home(self):
        self.old.mkdir(parents=True)
        os.environ["BRAINRC_HOME"] = str(self.old)
        self.assertEqual(self.config.former_homes(), [])
        self.assertIsNone(self.config.unmigrated_home())

    def test_brainrc_home_symlinked_to_the_legacy_dir_is_not_a_former_home(self):
        self.old.mkdir(parents=True)
        link = self.tmp / "x"
        link.symlink_to(self.old)
        os.environ["BRAINRC_HOME"] = str(link)
        self.assertEqual(self.config.former_homes(), [])

    def test_broken_legacy_symlink_counts_as_absent(self):
        self.old.parent.mkdir(parents=True)
        self.old.symlink_to(self.tmp / "gone")
        self.assertIsNone(self.config.unmigrated_home())

    def test_unmigrated_home_names_which_old_home(self):
        self.assertIsNone(self.config.unmigrated_home())
        self.old.mkdir(parents=True)
        self.assertEqual(self.config.unmigrated_home(), ("legacy", self.old))
        os.environ["AICFG_HOME"] = str(self.tmp / "y")
        self.assertEqual(self.config.unmigrated_home(), ("env", self.tmp / "y"))
        os.environ["BRAINRC_HOME"] = str(self.tmp / "x")
        self.assertIsNone(self.config.unmigrated_home())


if __name__ == "__main__":
    unittest.main()
