"""Doctor's copy-paste `rm` fixes quote the path but leave `~` for the shell to expand (#105)."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from brainrc.doctor import _home_findings, _link_finding, shell_path
from brainrc.plan import Link

HOME_VARS = ("HOME", "BRAINRC_HOME", "AICFG_HOME", "XDG_CONFIG_HOME")


class ShellPathTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name).resolve() / "my home"
        self.home.mkdir()
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_plain_paths_are_unchanged(self):
        self.assertEqual(shell_path(self.home / ".claude/skills/review"), "~/.claude/skills/review")
        self.assertEqual(shell_path(self.home), "~")

    def test_spaces_and_quotes_are_quoted_after_the_tilde(self):
        self.assertEqual(shell_path(self.home / "My Skills/it's"), "~/'My Skills/it'\"'\"'s'")
        self.assertEqual(shell_path(Path("/opt/a b/c")), "'/opt/a b/c'")

    def test_the_shell_reads_back_the_same_path(self):
        for path in (self.home / "My Skills/it's", self.home / "a;rm -rf x", Path("/opt/a b/$HOME")):
            out = subprocess.run(["sh", "-c", f"printf %s {shell_path(path)}"], capture_output=True,
                                 text=True, env={"HOME": str(self.home), "PATH": os.environ["PATH"]})
            self.assertEqual(out.stdout, str(path))


class DoctorFixQuotingTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name).resolve() / "home"
        self.home.mkdir()

    def env(self):
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env["HOME"] = str(self.home)
        return mock.patch.dict(os.environ, env, clear=True)

    def test_broken_link_fix_quotes_the_link(self):
        dest = self.home / "Skills Dir" / "review"
        dest.parent.mkdir()
        dest.symlink_to(self.home / "gone repo" / "review")
        with self.env():
            level, what, fix = _link_finding(Link("claude", dest, self.home / "repo/skills/review"), [])
        self.assertEqual(level, "FAIL")
        self.assertTrue(fix.startswith("rm ~/'Skills Dir/review' && "), fix)

    def test_unused_old_home_fix_quotes_the_dir(self):
        old = self.home / "old home"
        old.mkdir()
        new = self.home / ".config" / "brainrc"
        new.mkdir(parents=True)
        (new / "instructions.md").write_text("x\n")
        with self.env(), mock.patch.dict(os.environ, {"AICFG_HOME": str(old)}):
            [(level, what, fix)] = _home_findings()
        self.assertEqual(level, "WARN")
        self.assertTrue(fix.endswith("then remove it: rm -r ~/'old home'"), fix)

if __name__ == "__main__":
    unittest.main()
