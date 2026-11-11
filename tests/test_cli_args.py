"""The argparse CLI (#125): help and version exit 0, per-command help, hidden maintainer commands,
and `status` / `apply` limited to some harnesses with `--only`."""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))
import brainrc  # noqa: E402
from test_brainrc import TempRepoCase, copy_repo, home_files, install_harnesses, quiet  # noqa: E402


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = brainrc.cli.main(["brainrc", *args])
    return code, out.getvalue(), err.getvalue()


class HelpTest(unittest.TestCase):
    def test_help_and_version_exit_zero(self):
        for args in (["--help"], ["-h"], ["--version"]):
            code, out, _ = run(*args)
            self.assertEqual(code, 0, args)
            self.assertTrue(out, args)

    def test_each_command_has_its_own_help(self):
        for cmd in ("init", "status", "apply", "update", "uninstall", "validate", "doctor", "migrate", "tokens"):
            code, out, _ = run(cmd, "--help")
            self.assertEqual(code, 0, cmd)
            self.assertIn(f" {cmd} ", out.splitlines()[0] + " ")
        self.assertIn("--only", run("apply", "--help")[1])
        self.assertIn("--only", run("status", "--help")[1])
        self.assertIn("--pack", run("validate", "--help")[1])
        self.assertIn("--dry-run", run("migrate", "--help")[1])

    def test_maintainer_commands_are_hidden_but_still_run(self):
        _, out, _ = run("--help")
        for cmd in ("status", "apply", "doctor", "validate"):
            self.assertIn(cmd, out)
        self.assertNotIn("plugin", out)
        self.assertNotIn("release", out)
        version = (REPO / "VERSION").read_text().strip()
        code, notes, _ = run("release", "--notes", version)
        self.assertEqual(code, 0)
        self.assertTrue(notes.strip())
        self.assertEqual(run("release", "--help")[0], 0)

    def test_usage_errors_exit_two_on_stderr(self):
        for args in (["bogus"], ["apply", "--bogus"], ["validate", "--pack"], ["--version", "status"],
                     ["release", "--dry-run", "--notes", "1.0.0"]):
            code, out, err = run(*args)
            self.assertEqual(code, 2, args)
            self.assertEqual(out, "", args)
            self.assertIn("usage:", err + out, args)

    def test_help_names_the_installed_command(self):
        with mock.patch("brainrc.config.installed", return_value=True):
            _, out, _ = run("apply", "--help")
        self.assertTrue(out.startswith("usage: brainrc apply"), out)
        self.assertNotIn("scripts/brainrc.py", out)
        _, out, _ = run("apply", "--help")
        self.assertTrue(out.startswith("usage: python3 scripts/brainrc.py apply"), out)

    def test_checkout_script_help_exits_zero(self):
        result = subprocess.run([sys.executable, str(REPO / "scripts/brainrc.py"), "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("doctor", result.stdout)


class OnlyTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        install_harnesses(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def touched(self) -> set[str]:
        """The top-level entries of HOME that hold a file or link apply wrote."""
        return {p.relative_to(self.home).parts[0] for p in home_files(self.home)}

    def test_apply_only_claude_touches_only_claude(self):
        code, out, _ = run("apply", "--only", "claude")
        self.assertEqual(code, 0, out)
        self.assertLessEqual(self.touched(), {".claude", ".claude.json"})
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())
        self.assertIn("hooks", (self.home / ".claude/settings.json").read_text())

    def test_status_only_reports_only_that_harness(self):
        code, out, _ = run("status", "--only", "codex")
        self.assertEqual(code, 0, out)
        self.assertIn("codex", out)
        self.assertNotIn(" claude ", out)
        self.assertNotIn(".claude", out)
        self.assertEqual(home_files(self.home), [])

    def test_several_harnesses_by_repeat_or_comma(self):
        for args in (["--only", "claude", "--only", "codex"], ["--only", "claude,codex"]):
            code, out, _ = run("status", *args)
            self.assertEqual(code, 0, out)
            self.assertIn(".claude/", out)
            self.assertIn(".codex/", out)
            self.assertNotIn(".cursor/", out)

    def test_unknown_or_disabled_harness_is_an_error_and_writes_nothing(self):
        code, out, _ = run("apply", "--only", "nope")
        self.assertEqual(code, 2)
        self.assertIn("no such harness", out)
        code, out, _ = run("apply", "--only", "gemini")  # disabled in harnesses.toml
        self.assertEqual(code, 2)
        self.assertIn("disabled", out)
        self.assertEqual(home_files(self.home), [])
        self.assertFalse(self.settings_home.exists())

    def test_a_broken_harnesses_file_fails_as_without_only(self):
        (self.repo / "harnesses.local.toml").write_text("[claude\n")
        code, out, _ = run("apply", "--only", "claude")
        self.assertEqual(code, 1)
        self.assertIn("invalid TOML", out)

    def test_other_harnesses_keep_their_links_and_hooks(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "skills/spec-agent").rename(self.repo / "skills/spec-agent-moved")
        code, out, _ = run("apply", "--only", "codex")
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".codex/skills/spec-agent").is_symlink())  # pruned in codex
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())  # left in claude
        self.assertTrue((self.home / ".cursor/skills/spec-agent").is_symlink())
        self.assertIn("brainrc", (self.home / ".claude/settings.json").read_text())

    def test_disabled_harness_cleanup_waits_for_a_full_apply(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        run("apply", "--only", "codex")
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())
        quiet(brainrc.cmd_sync, True)
        self.assertFalse((self.home / ".claude/skills/spec-agent").is_symlink())

    def test_scope_ends_with_the_command(self):
        run("status", "--only", "claude")
        self.assertIsNone(brainrc.config.harness_scope())


class OnlyInstalledTest(TempRepoCase):
    """From a package, the hooks copy serves every harness, so --only never prunes it."""

    def setUp(self):
        super().setUp()
        self.pkg = Path(tempfile.mkdtemp()) / "brainrc"
        copy_repo(self.pkg / "_core")
        brainrc.config.REPO = self.pkg / "_core"
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        install_harnesses(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        shutil.rmtree(self.pkg.parent)
        super().tearDown()

    def test_only_a_harness_without_hooks_keeps_the_hooks_copy(self):
        quiet(brainrc.cmd_sync, True)
        copy = self.settings_home / "hooks/core"
        self.assertTrue(copy.is_dir())
        code, out, _ = run("apply", "--only", "codex")
        self.assertEqual(code, 0, out)
        self.assertNotIn("PRUNE", out)
        self.assertTrue(copy.is_dir())
        self.assertTrue((self.home / ".claude/hooks/brainrc").resolve().is_dir())


if __name__ == "__main__":
    unittest.main()
