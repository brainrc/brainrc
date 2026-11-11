"""`brainrc init` (#127): pick the harnesses to manage, and adopt existing instruction files."""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, home_files, quiet  # noqa: E402

from brainrc.init import set_enabled  # noqa: E402


def run(*args: str, stdin: str | None = None, tty: bool = False) -> tuple[int, str]:
    out = io.StringIO()
    feed = io.StringIO(stdin or "")
    feed.isatty = lambda: tty
    with contextlib.redirect_stdout(out), mock.patch("sys.stdin", feed):
        code = brainrc.cli.main(["brainrc", "init", *args])
    return code, out.getvalue()


class SetEnabledTest(unittest.TestCase):
    def test_adds_a_table_to_an_empty_file(self):
        self.assertEqual(set_enabled("", "codex", False), "[codex]\nenabled = false\n")

    def test_appends_after_one_blank_line(self):
        for text in ("# mine\n", "# mine", "# mine\n\n\n"):
            self.assertEqual(set_enabled(text, "codex", True), "# mine\n\n[codex]\nenabled = true\n")

    def test_replaces_enabled_in_its_own_table_only(self):
        text = '[claude]\nenabled = true\n\n[codex]\nskills = "~/x"\nenabled = true  # on\n'
        after = set_enabled(text, "codex", False)
        self.assertEqual(after, '[claude]\nenabled = true\n\n[codex]\nskills = "~/x"\nenabled = false\n')

    def test_adds_enabled_to_an_existing_table(self):
        after = set_enabled('# keep\n[cursor]\nhome = "~/.c"\n', "cursor", False)
        self.assertEqual(after, '# keep\n[cursor]\nenabled = false\nhome = "~/.c"\n')
        self.assertEqual(tomllib.loads(after)["cursor"], {"enabled": False, "home": "~/.c"})


class InitTest(TempRepoCase):
    """A fresh HOME with Claude Code and Codex installed, each with an instructions file."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        (self.home / ".claude").mkdir()
        (self.home / ".codex").mkdir()
        self.claude_md = self.home / ".claude/CLAUDE.md"
        self.claude_md.write_text("Always answer in haiku.\n")

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def local(self) -> dict:
        path = self.repo / "harnesses.local.toml"
        return tomllib.loads(path.read_text()) if path.exists() else {}

    def backups(self, d: str) -> list[Path]:
        return sorted((self.home / d).glob("*.bak-brainrc-*"))

    def test_init_then_apply_has_no_conflict_and_keeps_the_users_text(self):
        code, out = run("--yes")
        self.assertEqual(code, 0, out)
        self.assertFalse(self.claude_md.exists())
        [backup] = self.backups(".claude")
        self.assertEqual(backup.read_text(), "Always answer in haiku.\n")
        rule = self.repo / "rules/adopted-claude.local.md"
        self.assertIn("Always answer in haiku.", rule.read_text())
        self.assertIn("rules/adopted-claude.local.md", out)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("CONFLICT", out)
        self.assertTrue(self.claude_md.is_symlink())
        self.assertIn("Always answer in haiku.", self.claude_md.read_text())
        self.assertIn("Always answer in haiku.", (self.home / ".codex/AGENTS.md").read_text())

    def test_without_init_apply_reports_the_conflict(self):
        _, out = quiet(brainrc.cmd_sync, False)
        self.assertIn("CONFLICT", out)

    def test_yes_manages_every_installed_harness_and_writes_nothing_new(self):
        code, out = run("--yes")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.local(), {})
        self.assertIn("brainrc manages claude, codex", out)
        self.assertIn("not installed", out)

    def test_harness_writes_enabled_and_keeps_the_rest_of_the_file(self):
        (self.repo / "harnesses.local.toml").write_text('# my notes\n[claude]\nskills = "~/.claude/skills"\n')
        code, out = run("--harness", "claude", "--harness", "gemini")
        self.assertEqual(code, 0, out)
        text = (self.repo / "harnesses.local.toml").read_text()
        self.assertTrue(text.startswith("# my notes\n"))
        self.assertEqual(self.local()["codex"], {"enabled": False})
        self.assertEqual(self.local()["gemini"], {"enabled": True})  # disabled in harnesses.toml
        self.assertNotIn("enabled", self.local()["claude"])
        self.assertFalse(self.claude_md.exists())
        code, out = run("--harness", "claude,gemini")
        self.assertIn("needs no change", out)

    def test_an_unknown_harness_is_an_error_and_writes_nothing(self):
        code, out = run("--harness", "nope")
        self.assertEqual(code, 2)
        self.assertIn("no such harness", out)
        self.assertTrue(self.claude_md.is_file())
        self.assertFalse((self.repo / "harnesses.local.toml").exists())

    def test_dry_run_writes_nothing(self):
        before = home_files(self.home)
        code, out = run("--harness", "claude", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("Would write", out)
        self.assertIn("Would move ~/.claude/CLAUDE.md", out)
        self.assertEqual(home_files(self.home), before)
        self.assertFalse((self.repo / "harnesses.local.toml").exists())
        self.assertFalse((self.repo / "rules/adopted-claude.local.md").exists())

    def test_no_adopt_leaves_the_file_and_says_so(self):
        code, out = run("--yes", "--no-adopt")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.claude_md.read_text(), "Always answer in haiku.\n")
        self.assertIn("Left ~/.claude/CLAUDE.md in place", out)

    def test_same_text_in_two_files_is_adopted_once(self):
        (self.home / ".codex/AGENTS.md").write_text("Always answer in haiku.\n")
        code, out = run("--yes")
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(p.name for p in (self.repo / "rules").glob("adopted-*")),
                         ["adopted-claude.local.md"])
        self.assertEqual(len(self.backups(".codex")), 1)
        self.assertIn("already adopted", out)

    def test_running_init_again_on_a_restored_file_adds_no_second_rule(self):
        run("--yes")
        self.claude_md.write_text("Always answer in haiku.\n")
        code, out = run("--yes")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(list((self.repo / "rules").glob("adopted-*"))), 1)
        self.assertIn("already adopted", out)

    def test_different_text_gets_its_own_rule(self):
        run("--yes")
        self.claude_md.write_text("Now answer in limericks.\n")
        run("--yes")
        rules = sorted(p.name for p in (self.repo / "rules").glob("adopted-*"))
        self.assertEqual(rules, ["adopted-claude-2.local.md", "adopted-claude.local.md"])

    def test_an_empty_file_or_a_dangling_link_is_moved_without_a_rule(self):
        self.claude_md.write_text("  \n")
        (self.home / ".codex/AGENTS.md").symlink_to(self.home / "gone.md")
        code, out = run("--yes")
        self.assertEqual(code, 0, out)
        self.assertEqual(list((self.repo / "rules").glob("adopted-*")), [])
        self.assertTrue(self.backups(".codex")[0].is_symlink())
        self.assertIn("it was empty", out)
        _, out = quiet(brainrc.cmd_sync, True)
        self.assertNotIn("CONFLICT", out)

    def test_a_link_brainrc_made_is_left_alone(self):
        self.claude_md.unlink()
        quiet(brainrc.cmd_sync, True)
        code, out = run("--yes")
        self.assertEqual(code, 0, out)
        self.assertTrue(self.claude_md.is_symlink())
        self.assertNotIn("Moved", out)
        self.assertEqual(self.backups(".claude"), [])

    def test_a_link_to_the_users_own_file_is_moved_and_its_target_kept(self):
        mine = self.home / "notes.md"
        mine.write_text("Prefer tabs.\n")
        self.claude_md.unlink()
        self.claude_md.symlink_to(mine)
        run("--yes")
        self.assertEqual(mine.read_text(), "Prefer tabs.\n")
        self.assertTrue(self.backups(".claude")[0].is_symlink())
        self.assertIn("Prefer tabs.", (self.repo / "rules/adopted-claude.local.md").read_text())

    def test_without_a_terminal_it_asks_for_yes_or_harness(self):
        code, out = run()
        self.assertEqual(code, 2)
        self.assertIn("--yes", out)
        self.assertTrue(self.claude_md.is_file())

    def test_interactive_answers_choose_harnesses_and_adoptions(self):
        code, out = run(stdin="y\nn\nn\n", tty=True)  # manage claude, not codex; keep CLAUDE.md
        self.assertEqual(code, 0, out)
        self.assertEqual(self.local(), {"codex": {"enabled": False}})
        self.assertTrue(self.claude_md.is_file())
        self.assertIn("Left ~/.claude/CLAUDE.md in place", out)

    def test_interactive_end_of_input_takes_the_defaults(self):
        code, out = run(stdin="", tty=True)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.local(), {})
        self.assertFalse(self.claude_md.exists())

    def test_init_is_refused_while_an_old_home_is_unmigrated(self):
        with mock.patch("brainrc.config.unmigrated_home", return_value=("dir", self.home / "old")):
            code, out = run("--yes")
        self.assertEqual(code, 1)
        self.assertIn("migrate", out)
        self.assertTrue(self.claude_md.is_file())


if __name__ == "__main__":
    unittest.main()
