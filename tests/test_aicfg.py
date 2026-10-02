"""Tests for scripts/aicfg.py: settings merge, sync against a fake HOME, and validation."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("aicfg", REPO / "scripts" / "aicfg.py")
aicfg = importlib.util.module_from_spec(spec)
sys.modules["aicfg"] = aicfg  # dataclasses look the module up while decorating
spec.loader.exec_module(aicfg)

FOREIGN = {"hooks": [{"type": "command", "command": "node /opt/other/hook.js"}]}
OURS_OLD = {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/ai-config/old.py"}]}
SOURCES = ("skills", "agents", "commands", "overrides", "rules")
FRAGMENT = REPO / "overrides/claude/settings.fragment.json"


def quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*args)
    return code, buf.getvalue()


def copy_repo(dest: Path) -> None:
    """Sources plus the committed harnesses.toml only: never the developer's *.local.* files."""
    for name in SOURCES:
        shutil.copytree(REPO / name, dest / name, symlinks=True,
                        ignore=shutil.ignore_patterns("*.local.md", "__pycache__"))
    shutil.copy2(REPO / "harnesses.toml", dest / "harnesses.toml")


class TempRepoCase(unittest.TestCase):
    """Point aicfg at a throwaway copy of the repo, so tests never read local config or write dist/."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        copy_repo(self.repo)
        self.old_repo = aicfg.REPO
        aicfg.REPO = self.repo

    def tearDown(self):
        aicfg.REPO = self.old_repo
        shutil.rmtree(self.repo)


class MergeSettingsTest(unittest.TestCase):
    def setUp(self):
        self.fragment = aicfg.SettingsMerge("claude", Path("unused"), FRAGMENT, "~/.claude/hooks/ai-config").wanted()

    def test_renders_hooks_dir_placeholder(self):
        commands = [h["command"] for g in self.fragment["hooks"]["PreToolUse"] for h in g["hooks"]]
        self.assertIn('python3 "$HOME/.claude/hooks/ai-config/guard_outward.py"', commands)
        self.assertFalse(any(aicfg.HOOKS_DIR_PLACEHOLDER in c for c in commands))

    def test_custom_hooks_dir_is_owned(self):
        m = aicfg.SettingsMerge("claude", Path("unused"), FRAGMENT, "/opt/hooks/mine")
        once = aicfg.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, m.wanted(), m.markers())
        self.assertEqual(aicfg.merge_settings(once, m.wanted(), m.markers()), once)
        self.assertIn("/opt/hooks/mine/guard_outward.py", json.dumps(once))

    def test_preserves_foreign_hooks_and_other_keys(self):
        current = {"tui": "fullscreen", "hooks": {"SessionStart": [FOREIGN], "PreToolUse": [FOREIGN]}}
        merged = aicfg.merge_settings(current, self.fragment)
        self.assertEqual(merged["tui"], "fullscreen")
        self.assertEqual(merged["hooks"]["SessionStart"], [FOREIGN])
        self.assertEqual(merged["hooks"]["PreToolUse"][0], FOREIGN)
        self.assertEqual(len(merged["hooks"]["PreToolUse"]), 1 + len(self.fragment["hooks"]["PreToolUse"]))

    def test_idempotent(self):
        once = aicfg.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, self.fragment)
        self.assertEqual(aicfg.merge_settings(once, self.fragment), once)

    def test_replaces_stale_owned_groups(self):
        merged = aicfg.merge_settings({"hooks": {"PostToolUse": [OURS_OLD]}}, self.fragment)
        self.assertNotIn("PostToolUse", merged["hooks"])
        self.assertNotIn(OURS_OLD, merged["hooks"]["PreToolUse"])

    def test_does_not_mutate_input(self):
        current = {"hooks": {"PreToolUse": [FOREIGN]}}
        aicfg.merge_settings(current, self.fragment)
        self.assertEqual(current, {"hooks": {"PreToolUse": [FOREIGN]}})


class SyncFakeHomeTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def test_status_writes_nothing(self):
        code, out = quiet(aicfg.cmd_sync, False)
        self.assertEqual(code, 0)
        self.assertIn("Dry run", out)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse((self.repo / "dist").exists())

    def test_relative_symlink_into_repo_is_ok(self):
        quiet(aicfg.cmd_sync, True)
        link = self.home / ".claude/skills/spec-agent"
        link.unlink()
        link.symlink_to(os.path.relpath(self.repo / "skills/spec-agent", link.parent))
        self.assertEqual(aicfg.Link("claude", link, self.repo / "skills/spec-agent").state(), "ok")

    def test_updates_moved_links_and_prunes_dangling(self):
        quiet(aicfg.cmd_sync, True)
        skills_dir = self.home / ".claude/skills"
        (skills_dir / "spec-agent").unlink()
        (skills_dir / "spec-agent").symlink_to(self.repo / "skills/terraform")  # points at wrong skill
        (skills_dir / "gone").symlink_to(self.repo / "skills/gone")  # removed from the repo
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0)
        self.assertIn("UPDATE", out)
        self.assertIn("PRUNE", out)
        self.assertEqual(aicfg.link_target(skills_dir / "spec-agent"), self.repo / "skills/spec-agent")
        self.assertFalse((skills_dir / "gone").is_symlink())

    def test_invalid_settings_json_is_a_conflict(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        settings.write_text("{ not json")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1)
        self.assertIn("invalid JSON", out)
        self.assertEqual(settings.read_text(), "{ not json")

    def test_backups_are_capped(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        for n in range(aicfg.BACKUPS_KEPT + 3):
            (settings.parent / f"settings.json.bak-aicfg-2026010{n}T000000Z").write_text("{}")
        settings.write_text("{}")
        quiet(aicfg.cmd_sync, True)
        self.assertEqual(len(list(settings.parent.glob("settings.json.bak-aicfg-*"))), aicfg.BACKUPS_KEPT)
        self.assertEqual(list(settings.parent.glob(".settings.json.aicfg-tmp")), [])

    def test_apply_then_in_sync_and_conflicts_respected(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        settings.write_text(json.dumps({"hooks": {"SessionStart": [FOREIGN]}}))
        (self.home / ".codex").mkdir()
        (self.home / ".codex/AGENTS.md").write_text("mine\n")

        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1)  # the pre-existing codex file is a conflict
        self.assertIn("CONFLICT", out)
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text(), "mine\n")

        skill = self.home / ".claude/skills/spec-agent"
        self.assertTrue(skill.is_symlink())
        self.assertTrue((skill / "roles" / "implementer.md").is_file())
        self.assertTrue((self.home / ".claude/hooks/ai-config/guard_outward.py").is_file())

        merged = json.loads(settings.read_text())
        self.assertEqual(merged["hooks"]["SessionStart"], [FOREIGN])
        self.assertTrue(any(aicfg._owned(g) for g in merged["hooks"]["PreToolUse"]))
        self.assertEqual(len(list(settings.parent.glob("settings.json.bak-aicfg-*"))), 1)

        (self.home / ".codex/AGENTS.md").unlink()
        quiet(aicfg.cmd_sync, True)
        code, out = quiet(aicfg.cmd_sync, False)
        self.assertEqual((code, out.strip()), (0, "Everything in sync."))


class ValidateTest(unittest.TestCase):
    def test_repo_is_valid(self):
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_catches_placeholder_without_hooks_dir(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            copy_repo(tmp)
            toml = tmp / "harnesses.toml"
            toml.write_text(toml.read_text().replace('hooks_dir = "~/.claude/hooks/ai-config"\n', ""))
            old = aicfg.REPO
            aicfg.REPO = tmp
            try:
                code, out = quiet(aicfg.cmd_validate)
            finally:
                aicfg.REPO = old
            self.assertEqual(code, 1)
            self.assertIn("has no hooks_dir", out)
        finally:
            shutil.rmtree(tmp)

    def test_catches_broken_references(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            copy_repo(tmp)
            skill = tmp / "skills/spec-agent/SKILL.md"
            skill.write_text(skill.read_text() + "\n[agent: ghost] [x](missing.md) the `nope` skill\n")
            (tmp / "agents/verifier.md").write_text(
                (tmp / "agents/verifier.md").read_text().replace("model: haiku", "model: gpt-9"))
            old = aicfg.REPO
            aicfg.REPO = tmp
            try:
                code, out = quiet(aicfg.cmd_validate)
            finally:
                aicfg.REPO = old
            self.assertEqual(code, 1)
            for expected in ("unknown agent `ghost`", "broken link `missing.md`",
                             "unknown skill `nope`", "unknown model `gpt-9`"):
                self.assertIn(expected, out)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
