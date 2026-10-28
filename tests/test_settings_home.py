"""Contract tests for the settings home: resolution order, legacy fallback, warnings (spec 206, AC1-AC6).

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
HOME_VARS = ("HOME", "BRAINRC_HOME", "AICFG_HOME", "XDG_CONFIG_HOME", "PYTHONWARNINGS")


class HomeCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.new = self.home / ".config" / "brainrc"
        self.old = self.home / ".config" / "ai-config"

    def run_cli(self, *args, home=None, **env_vars):
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env["HOME"] = str(home or self.home)
        env.update(env_vars)
        return subprocess.run(
            [sys.executable, "scripts/brainrc.py", *args], cwd=REPO, env=env,
            capture_output=True, text=True, timeout=120,
        )

    def ok(self, *args, **kw):
        proc = self.run_cli(*args, **kw)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def stderr_lines(self, proc):
        return [line for line in proc.stderr.splitlines() if line.strip()]


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

    def test_ac3_absolute_xdg_with_only_legacy_dir_uses_legacy_and_warns(self):
        self.old.mkdir(parents=True)
        xdg = self.tmp / "xdg"
        proc = self.ok("apply", XDG_CONFIG_HOME=str(xdg))
        self.assertTrue((self.old / "instructions.md").is_file())
        self.assertFalse((xdg / "brainrc").exists())
        self.assertEqual(proc.stderr.count("brainrc migrate"), 1, proc.stderr)

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
    def test_ac4_legacy_only_dir_is_used_and_warns_once_on_stderr(self):
        self.old.mkdir(parents=True)
        proc = self.ok("apply")
        self.assertTrue((self.old / "instructions.md").is_file())
        self.assertFalse(self.new.exists())
        lines = self.stderr_lines(proc)
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertIn(".config/ai-config", lines[0])
        self.assertIn("brainrc migrate", lines[0])
        self.assertNotIn("brainrc migrate", proc.stdout)

    def test_ac4_status_in_legacy_home_warns_once_and_keeps_exit_code(self):
        self.old.mkdir(parents=True)
        self.ok("apply")
        proc = self.ok("status")
        lines = self.stderr_lines(proc)
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertIn(".config/ai-config", lines[0])
        self.assertIn("brainrc migrate", lines[0])
        self.assertNotIn("migrate", proc.stdout)

    def test_ac4_stdout_matches_a_default_home_install(self):
        self.old.mkdir(parents=True)
        other = self.tmp / "other"
        other.mkdir()
        legacy = self.ok("apply")
        default = self.ok("apply", home=other)
        self.assertIn("brainrc migrate", legacy.stderr)
        self.assertTrue((other / ".config" / "brainrc" / "instructions.md").is_file())
        self.assertEqual(legacy.stdout, default.stdout)
        self.assertEqual(self.ok("status").stdout, self.ok("status", home=other).stdout)


class TestAicfgHomeEnv(HomeCase):
    def test_ac5_aicfg_home_is_used_and_warns_once_naming_brainrc_home(self):
        y = self.tmp / "y"
        proc = self.ok("apply", AICFG_HOME=str(y))
        self.assertTrue((y / "instructions.md").is_file())
        self.assertFalse(self.new.exists())
        lines = self.stderr_lines(proc)
        self.assertEqual(len(lines), 1, proc.stderr)
        self.assertIn("BRAINRC_HOME", lines[0])
        self.assertNotIn("BRAINRC_HOME", proc.stdout)

    def test_ac5_status_warns_once_never_on_stdout(self):
        y = self.tmp / "y"
        self.ok("apply", AICFG_HOME=str(y))
        proc = self.ok("status", AICFG_HOME=str(y))
        self.assertEqual(proc.stderr.count("BRAINRC_HOME"), 1, proc.stderr)
        self.assertEqual(len(self.stderr_lines(proc)), 1, proc.stderr)
        self.assertNotIn("AICFG_HOME", proc.stdout)

    def test_ac5_version_does_not_warn(self):
        proc = self.ok("--version", AICFG_HOME=str(self.tmp / "y"))
        self.assertEqual(proc.stderr, "")

    def test_ac5_version_does_not_warn_for_legacy_dir(self):
        self.old.mkdir(parents=True)
        proc = self.ok("--version")
        self.assertEqual(proc.stderr, "")


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
        self.tmp = Path(tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.old = self.home / ".config" / "ai-config"
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env["HOME"] = str(self.home)
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
        self.assertEqual(self.config.home_origin(), "brainrc_env")

    def test_brainrc_home_symlinked_to_the_legacy_dir_is_not_a_former_home(self):
        self.old.mkdir(parents=True)
        link = self.tmp / "x"
        link.symlink_to(self.old)
        os.environ["BRAINRC_HOME"] = str(link)
        self.assertEqual(self.config.former_homes(), [])

    def test_broken_legacy_symlink_counts_as_absent(self):
        self.old.parent.mkdir(parents=True)
        self.old.symlink_to(self.tmp / "gone")
        self.assertEqual(self.config.home_origin(), "default")


if __name__ == "__main__":
    unittest.main()
