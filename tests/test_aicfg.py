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


def quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*args)
    return code, buf.getvalue()


class MergeSettingsTest(unittest.TestCase):
    def setUp(self):
        self.fragment = json.loads((REPO / "overrides/claude/settings.fragment.json").read_text())

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


class SyncFakeHomeTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)

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

    def test_catches_broken_references(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            for name in ("skills", "agents", "commands", "overrides", "rules"):
                shutil.copytree(REPO / name, tmp / name, symlinks=True)
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
