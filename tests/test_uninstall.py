"""`brainrc uninstall` (#128): take out what apply put into the harnesses, and nothing else."""
import contextlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, copy_repo, install_harnesses, quiet  # noqa: E402
from support import home_env, readlink, restore_home, rmtree, saved_home, symlink  # noqa: E402

BACKUP = re.compile(r"\.bak-brainrc-\d{8}T\d{6}Z$")
SETTINGS = {"theme": "dark", "hooks": {"PreToolUse": [
    {"matcher": "Bash", "hooks": [{"type": "command", "command": "~/bin/mine.sh"}]}]}}


def run(*args: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = brainrc.cli.main(["brainrc", *args])
    return code, out.getvalue()


def snapshot(home: Path) -> dict[str, object]:
    """Every dir, file and link under home, JSON files parsed; brainrc's backups left out."""
    found: dict[str, object] = {}
    for p in sorted(home.rglob("*")):
        rel = p.relative_to(home).as_posix()
        if BACKUP.search(p.name):
            continue
        if p.is_symlink():
            found[rel] = ("link", readlink(p))
        elif p.is_dir():
            found[rel] = "dir"
        elif p.suffix == ".json":
            found[rel] = json.loads(p.read_text())
        else:
            found[rel] = p.read_text()
    return found


class UninstallTest(TempRepoCase):
    """Every harness installed, with some of the user's own settings, hooks and MCP servers."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        (self.repo / "mcp").mkdir(exist_ok=True)
        (self.repo / "mcp/servers.toml").write_text('[servers.docs]\nurl = "https://example.com/mcp"\n')
        self.settings = self.home / ".claude/settings.json"
        self.settings.write_text(json.dumps(SETTINGS))
        (self.home / ".claude.json").write_text(json.dumps({"numStartups": 3, "mcpServers": {"mine": {"command": "x"}}}))
        (self.home / ".codex/config.toml").write_text('model = "o3"\n')
        (self.home / ".claude/skills/my-skill").mkdir(parents=True)
        (self.home / ".claude/skills/my-skill/SKILL.md").write_text("mine\n")
        symlink(self.home / ".claude/skills/my-link", self.home / ".claude/skills/my-skill")

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        super().tearDown()

    def links(self) -> list[Path]:
        return [p for p in self.home.rglob("*") if p.is_symlink()]

    def test_configs_match_the_pre_apply_state_plus_the_users_later_edits(self):
        before = snapshot(self.home)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn("docs", (self.home / ".claude.json").read_text())
        self.assertTrue((self.home / ".cursor/hooks.json").is_file())
        settings = json.loads(self.settings.read_text())
        settings["model"] = "opus"  # the user's own edit after apply
        self.settings.write_text(json.dumps(settings))
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        before[".claude/settings.json"]["model"] = "opus"
        self.assertEqual(snapshot(self.home), before)
        self.assertIn("Uninstalled.", out)

    def test_the_settings_home_keeps_only_local_config(self):
        (self.repo / "packs.local.toml").write_text("")
        quiet(brainrc.cmd_sync, True)
        self.assertTrue((self.settings_home / "harnesses.json").is_file())
        run("uninstall")
        left = sorted(p.name for p in self.settings_home.rglob("*"))
        self.assertEqual(left, ["apply.lock"])
        self.assertTrue((self.repo / "packs.local.toml").is_file())

    def test_purge_deletes_the_settings_home(self):
        quiet(brainrc.cmd_sync, True)
        (self.settings_home / "packs/acme").mkdir(parents=True)  # a fetched git pack
        code, out = run("uninstall", "--purge")
        self.assertEqual(code, 0, out)
        self.assertIn("PURGE", out)
        self.assertFalse(self.settings_home.exists())
        self.assertEqual(self.links(), [self.home / ".claude/skills/my-link"])

    def test_dry_run_changes_nothing(self):
        quiet(brainrc.cmd_sync, True)
        before = snapshot(self.home)
        files = sorted(self.settings_home.rglob("*"))
        code, out = run("uninstall", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("REMOVE    claude    ~/.claude/skills/spec-agent", out.replace(str(self.home), "~"))
        self.assertIn("UNMERGE   claude    ~/.claude/settings.json  (hooks)", out.replace(str(self.home), "~"))
        self.assertIn("DELETE    cursor    ~/.cursor/hooks.json", out.replace(str(self.home), "~"))
        self.assertIn("Dry run.", out)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(sorted(self.settings_home.rglob("*")), files)

    def test_works_after_the_checkout_is_deleted(self):
        old = Path(tempfile.mkdtemp()).resolve() / "brainrc"
        copy_repo(old)
        brainrc.config.REPO = old
        quiet(brainrc.cmd_sync, True)
        rmtree(old.parent)
        brainrc.config.REPO = self.repo
        dangling = [p for p in self.links() if not p.exists()]
        self.assertTrue(dangling)
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.links(), [self.home / ".claude/skills/my-link"])
        self.assertEqual(json.loads(self.settings.read_text()), SETTINGS)

    def test_a_broken_harnesses_file_falls_back_to_the_manifest(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[claude\n")
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertIn("WARN", out)
        self.assertIn("harnesses.json", out)
        self.assertEqual(self.links(), [self.home / ".claude/skills/my-link"])

    def test_a_settings_file_it_cant_parse_is_left_and_reported(self):
        quiet(brainrc.cmd_sync, True)
        self.settings.write_text("{oops")
        code, out = run("uninstall")
        self.assertEqual(code, 1)
        self.assertIn("ERROR", out)
        self.assertIn("settings.json: invalid JSON", out)
        self.assertEqual(self.settings.read_text(), "{oops")
        self.assertFalse((self.home / ".claude/skills/spec-agent").is_symlink())

    def test_the_file_init_moved_aside_is_put_back(self):
        claude_md = self.home / ".claude/CLAUDE.md"
        claude_md.write_text("Always answer in haiku.\n")
        run("init", "--yes")
        quiet(brainrc.cmd_sync, True)
        self.assertTrue(claude_md.is_symlink())
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertIn("RESTORE", out)
        self.assertFalse(claude_md.is_symlink())
        self.assertEqual(claude_md.read_text(), "Always answer in haiku.\n")

    def test_nothing_applied_means_nothing_to_do(self):
        before = snapshot(self.home)
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertIn("Nothing to uninstall", out)
        self.assertEqual(snapshot(self.home), before)
        self.assertFalse(self.settings_home.exists())

    def test_a_second_uninstall_finds_nothing(self):
        quiet(brainrc.cmd_sync, True)
        run("uninstall")
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertIn("Nothing to uninstall", out)

    def test_apply_after_uninstall_reinstalls(self):
        quiet(brainrc.cmd_sync, True)
        run("uninstall")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())
        self.assertIn("brainrc", self.settings.read_text())

    def test_purge_never_deletes_a_settings_home_that_holds_other_files(self):
        config = self.home / ".config"
        (config / "nvim").mkdir(parents=True)
        (config / "nvim/init.lua").write_text("keep\n")
        os.environ["BRAINRC_HOME"] = str(config)
        quiet(brainrc.cmd_sync, True)
        code, out = run("uninstall", "--purge")
        self.assertEqual(code, 1, out)
        self.assertNotIn("PURGE", out)
        self.assertIn("--purge left ~/.config alone", out.replace(str(self.home), "~"))
        self.assertEqual((config / "nvim/init.lua").read_text(), "keep\n")
        self.assertFalse((config / "harnesses.json").exists())  # brainrc's own files still go
        self.assertFalse((self.home / ".claude/skills/spec-agent").is_symlink())

    def test_purge_never_deletes_home_or_a_harness_config(self):
        quiet(brainrc.cmd_sync, True)
        for home, reason in ((self.home, "home directory"), (self.home / ".config", "config directory"),
                             (self.home / ".config/opencode", "opencode's config"), (self.repo, "checkout")):
            os.environ["BRAINRC_HOME"] = str(home)
            code, out = run("uninstall", "--purge", "--dry-run")
            self.assertIn(reason, out)
            self.assertNotIn("PURGE", out)
        self.assertTrue((self.home / ".claude/skills/my-skill/SKILL.md").is_file())

    def test_purge_keeps_a_file_it_didnt_make_in_its_own_home(self):
        quiet(brainrc.cmd_sync, True)
        (self.settings_home / "notes.txt").write_text("mine\n")
        code, out = run("uninstall", "--purge")
        self.assertEqual(code, 1, out)
        self.assertIn("notes.txt", out)
        self.assertEqual((self.settings_home / "notes.txt").read_text(), "mine\n")

    def test_an_empty_folder_of_the_users_is_left_and_the_run_finishes(self):
        quiet(brainrc.cmd_sync, True)
        (self.home / ".cursor/skills/my-wip").mkdir()
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.home / ".cursor/skills/my-wip").is_dir())
        self.assertNotIn("RMDIR     cursor    ~/.cursor/skills\n", out.replace(str(self.home), "~"))
        self.assertFalse((self.settings_home / "harnesses.json").exists())

    def test_a_directory_that_fills_up_after_the_plan_is_reported_not_a_crash(self):
        quiet(brainrc.cmd_sync, True)
        steps, _, _ = brainrc.uninstall.plan_uninstall()
        rmdir = next(s for s in steps if s.action == "RMDIR")
        for s in steps[:steps.index(rmdir)]:
            s.run()
        (rmdir.path / "late").write_text("x")
        with unittest.mock.patch("brainrc.uninstall.plan_uninstall", return_value=([rmdir], [], [])):
            code, out = run("uninstall")
        self.assertEqual(code, 1, out)
        self.assertIn("FAILED", out)
        self.assertTrue((rmdir.path / "late").is_file())

    def test_manifest_entries_too_broad_to_trust_are_ignored(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[claude\n")  # only the manifest is left
        manifest = json.loads((self.settings_home / "harnesses.json").read_text())
        manifest["harnesses"]["claude"]["hooks_dir"] = "~/"
        manifest["harnesses"]["codex"]["skills"] = "/etc"
        manifest["roots"].append("/")
        (self.settings_home / "harnesses.json").write_text(json.dumps(manifest))
        code, out = run("uninstall", "--dry-run")
        self.assertIn("ignored harness 'claude': hooks_dir = '~/'", out)
        self.assertIn("ignored harness 'codex': skills = '/etc' is not inside ~", out)
        self.assertIn("ignored root '/'", out)
        self.assertNotIn("~/.claude/settings.json", out.replace(str(self.home), "~"))
        self.assertIn("~/.cursor/hooks.json", out.replace(str(self.home), "~"))


if __name__ == "__main__":
    unittest.main()
