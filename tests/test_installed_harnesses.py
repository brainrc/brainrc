"""apply touches only harnesses that are installed, and records them in a manifest (#126)."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, home_files, quiet  # noqa: E402


class InstalledHarnessTest(TempRepoCase):
    """A fresh HOME where only Claude Code is installed."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        (self.home / ".claude").mkdir()

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def top_level(self) -> set[str]:
        return {p.name for p in self.home.iterdir()}

    def manifest(self) -> dict:
        return json.loads((self.settings_home / "harnesses.json").read_text())

    def test_only_claude_installed_gets_only_claude_changes(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertLessEqual(self.top_level(), {".claude", ".claude.json"})
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())
        self.assertTrue((self.home / ".claude/settings.json").is_file())
        for name in ("codex (~/.codex)", "opencode (~/.config/opencode)", "cursor (~/.cursor)"):
            self.assertIn(name, out.replace(str(self.home), "~"))
        self.assertIn("Skipped, not installed", out)
        self.assertIn("enabled = true", out)
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertIn("Everything in sync.", out)

    def test_status_says_what_it_skips_and_writes_nothing(self):
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertIn("Skipped, not installed", out)
        self.assertNotIn(".codex/", out)
        self.assertEqual(home_files(self.home), [])
        self.assertFalse(self.settings_home.exists())

    def test_a_harness_installed_later_is_picked_up(self):
        quiet(brainrc.cmd_sync, True)
        (self.home / ".codex").mkdir()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.home / ".codex/skills/spec-agent").is_symlink())
        self.assertNotIn("codex (", out)

    def test_enabled_true_in_the_local_file_forces_a_harness(self):
        (self.repo / "harnesses.local.toml").write_text("[codex]\nenabled = true\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.home / ".codex/skills/spec-agent").is_symlink())
        self.assertFalse((self.home / ".cursor").exists())

    def test_a_harness_only_in_the_local_file_is_managed(self):
        (self.repo / "harnesses.local.toml").write_text('[mine]\nskills = "~/.mine/skills"\n')
        quiet(brainrc.cmd_sync, True)
        self.assertTrue((self.home / ".mine/skills/spec-agent").is_symlink())

    def test_home_key_sets_what_counts_as_installed(self):
        (self.repo / "harnesses.local.toml").write_text('[cursor]\nhome = "~/.cursor-app"\n')
        (self.home / ".cursor-app").mkdir()
        quiet(brainrc.cmd_sync, True)
        self.assertTrue((self.home / ".cursor/skills/spec-agent").is_symlink())

    def test_a_disabled_harness_is_not_reported_as_missing(self):
        (self.repo / "harnesses.local.toml").write_text("[cursor]\nenabled = false\n")
        _, out = quiet(brainrc.cmd_sync, False)
        self.assertNotIn("cursor (", out)

    def test_only_a_missing_harness_is_refused(self):
        code, out = quiet(brainrc.cli.main, ["brainrc", "apply", "--only", "codex"])
        self.assertEqual(code, 2)
        self.assertIn("isn't installed", out)
        self.assertIn("enabled = true", out)
        self.assertEqual(home_files(self.home), [])

    def test_doctor_is_clean_after_apply(self):
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_uninstalled_harness_is_never_recreated(self):
        (self.home / ".codex").mkdir()
        quiet(brainrc.cmd_sync, True)
        shutil.rmtree(self.home / ".codex")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".codex").exists())

    def test_apply_records_the_managed_harnesses(self):
        quiet(brainrc.cmd_sync, True)
        m = self.manifest()
        self.assertEqual(m["version"], 1)
        self.assertEqual(list(m["harnesses"]), ["claude"])
        self.assertEqual(m["harnesses"]["claude"]["skills"], "~/.claude/skills")
        self.assertNotIn("enabled", m["harnesses"]["claude"])
        self.assertEqual(m["roots"], [str(self.repo), str(self.repo / "packs/gatework")])

    def test_manifest_follows_full_applies_and_keeps_entries_outside_only(self):
        (self.home / ".codex").mkdir()
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(list(self.manifest()["harnesses"]), ["claude", "codex"])
        shutil.rmtree(self.home / ".codex")
        (self.home / ".cursor").mkdir()
        quiet(brainrc.cli.main, ["brainrc", "apply", "--only", "cursor"])
        self.assertEqual(list(self.manifest()["harnesses"]), ["claude", "codex", "cursor"])
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(list(self.manifest()["harnesses"]), ["claude", "cursor"])

    def test_manifest_keeps_a_moved_checkouts_old_root(self):
        quiet(brainrc.cmd_sync, True)
        moved = Path(tempfile.mkdtemp()) / "moved"
        shutil.copytree(self.repo, moved, symlinks=True)
        self.addCleanup(shutil.rmtree, moved.parent)
        brainrc.config.REPO = moved
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(self.manifest()["roots"], [str(moved), str(moved / "packs/gatework"),
                                                   str(self.repo), str(self.repo / "packs/gatework")])

    def test_an_unreadable_manifest_is_rewritten(self):
        self.settings_home.mkdir(parents=True)
        (self.settings_home / "harnesses.json").write_text("{not json")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(list(self.manifest()["harnesses"]), ["claude"])


if __name__ == "__main__":
    unittest.main()
