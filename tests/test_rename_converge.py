"""End to end: an install left by an older release (ai-config names) converges in one apply."""
import json
import os
import shutil
import tempfile
from pathlib import Path

from test_brainrc import TempRepoCase, brainrc, make_pack, quiet, set_core_version

GH = '[servers.gh]\ncommand = "npx"\nargs = ["-y", "@modelcontextprotocol/server-github"]\nenv_from = ["GH_TOKEN"]\n'
USER_CLAUDE_HOOK = "python3 ~/mine/ai-config-tools/check.py"  # path merely contains ai-config
USER_CURSOR_HOOK = "python3 ~/mine/ai-config-tools/cursor.py"


class OldInstallCase(TempRepoCase):
    """A fake HOME holding what an older release left behind, then one apply."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        os.environ["GH_TOKEN"] = "x"
        self.addCleanup(os.environ.pop, "GH_TOKEN", None)
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")
        (self.repo / "packs.local.toml").write_text(f'[acme]\npath = "{self.pack}"\n')
        (self.repo / "mcp").mkdir(exist_ok=True)
        (self.repo / "mcp/servers.toml").write_text(GH)
        for d in (".claude", ".cursor", ".codex", ".config/opencode", ".gemini/config"):
            (self.home / d).mkdir(parents=True)
        self.settings = self.home / ".claude/settings.json"
        self.hooks_json = self.home / ".cursor/hooks.json"
        self.claude_json = self.home / ".claude.json"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        shutil.rmtree(self.pack.parent)
        super().tearDown()

    def core_hooks(self, harness: str) -> Path:
        return self.repo / "overrides" / harness / "hooks"

    def seed_old_install(self, claude_target: Path | None = None) -> None:
        """Render a current apply, rewrite it to the old names, and add the user's own hooks."""
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        for path in (self.settings, self.hooks_json):
            path.write_text(path.read_text().replace("/hooks/brainrc", "/hooks/ai-config"))
        settings = json.loads(self.settings.read_text())
        settings["hooks"]["PreToolUse"].append({"hooks": [{"type": "command", "command": USER_CLAUDE_HOOK}]})
        self.settings.write_text(json.dumps(settings))
        cursor = json.loads(self.hooks_json.read_text())
        cursor["hooks"]["beforeShellExecution"].append({"command": USER_CURSOR_HOOK})
        self.hooks_json.write_text(json.dumps(cursor))
        claude = self.home / ".claude/hooks"
        for new, old in (("brainrc", "ai-config"), ("brainrc-acme", "ai-config-acme")):
            target = brainrc.link_target(claude / new)
            (claude / new).unlink()
            (claude / old).symlink_to(claude_target if (claude_target and new == "brainrc") else target)
        cursor_dir = self.home / ".cursor/hooks"
        target = brainrc.link_target(cursor_dir / "brainrc")
        (cursor_dir / "brainrc").unlink()
        (cursor_dir / "ai-config").symlink_to(target)

    def seed_backups(self) -> None:
        for path in (self.settings, self.hooks_json):
            for n in range(1, 7):
                path.with_name(f"{path.name}.bak-aicfg-2026010{n}T000000Z").write_text("{}")

    def seed_owned(self, home: Path) -> None:
        home.mkdir(parents=True, exist_ok=True)
        (home / "mcp-owned.json").write_text(json.dumps({str(self.claude_json): ["gh"]}))

    def old_gh_entry(self) -> None:
        self.claude_json.write_text(json.dumps({"mcpServers": {"gh": {
            "type": "stdio", "command": "npx", "args": ["-y", "old-github"]}}}))

    def commands(self, path: Path, event: str) -> list[str]:
        entries = json.loads(path.read_text())["hooks"][event]
        if path == self.settings:
            return [h["command"] for g in entries for h in g["hooks"]]
        return [e["command"] for e in entries]

    def all_commands(self, path: Path) -> list[str]:
        return [c for event in json.loads(path.read_text())["hooks"] for c in self.commands(path, event)]

    def assert_no_duplicates(self, path: Path) -> None:
        """A command may serve several events, but never twice in one."""
        for event in json.loads(path.read_text())["hooks"]:
            cmds = self.commands(path, event)
            self.assertEqual(len(cmds), len(set(cmds)), (event, cmds))

    def assert_converged(self, out: str = "") -> None:
        self.assertNotIn("CONFLICT", out)
        for path in (self.settings, self.hooks_json):
            self.assert_no_duplicates(path)
            cmds = self.all_commands(path)
            managed = [c for c in cmds if "ai-config-tools" not in c]
            self.assertFalse([c for c in managed if "hooks/ai-config" in c], managed)
            self.assertTrue(managed)
        pre = self.commands(self.settings, "PreToolUse")
        self.assertEqual(sum("hooks/brainrc/guard_outward.py" in c for c in pre), 1, pre)
        self.assertEqual(sum("hooks/brainrc-acme/guard_acme.py" in c for c in pre), 1, pre)
        self.assertEqual(pre.count(USER_CLAUDE_HOOK), 1)
        self.assertEqual(self.commands(self.hooks_json, "beforeShellExecution").count(USER_CURSOR_HOOK), 1)
        self.assertEqual(sorted(p.name for p in (self.home / ".claude/hooks").iterdir()),
                         ["brainrc", "brainrc-acme"])
        self.assertEqual(sorted(p.name for p in (self.home / ".cursor/hooks").iterdir()), ["brainrc"])
        for path in (self.settings, self.hooks_json):
            baks = sorted(path.parent.glob(f"{path.name}.bak-*"))
            self.assertLessEqual(len(baks), 5, [b.name for b in baks])
            self.assertTrue(any("bak-brainrc-" in b.name for b in baks), "newest backup kept")
            self.assertFalse(any("20260101T" in b.name for b in baks), "oldest backup pruned")
        servers = json.loads(self.claude_json.read_text())["mcpServers"]
        self.assertEqual(servers["gh"]["args"], ["-y", "@modelcontextprotocol/server-github"])
        self.assertEqual(self.claude_json.read_text().count('"gh"'), 1)
        self.assertEqual(quiet(brainrc.cmd_sync, False)[1].strip(), "Everything in sync.")
        self.assertEqual([f for f in brainrc.doctor_findings() if "hook" in f[1].lower() or "mcp" in f[1].lower()], [])

    def assert_second_apply_is_a_no_op(self) -> None:
        paths = [self.settings, self.hooks_json, self.claude_json]
        before = {p: p.read_text() for p in paths}
        names = sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*"))
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual({p: p.read_text() for p in paths}, before)
        self.assertEqual(sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*")), names)


class OldNameInstallTest(OldInstallCase):
    def test_one_apply_converges_with_the_record_in_the_resolved_home(self):
        self.seed_old_install()
        self.old_gh_entry()
        self.seed_owned(self.settings_home)
        self.seed_backups()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assert_converged(out)
        self.assert_second_apply_is_a_no_op()

    def test_one_apply_converges_with_the_record_only_in_the_former_home(self):
        self.seed_old_install()
        self.old_gh_entry()
        self.seed_owned(self.home / ".config/ai-config")
        self.seed_backups()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assert_converged(out)
        self.assert_second_apply_is_a_no_op()

    def test_cursor_hooks_json_from_old_name_entries_only(self):
        self.seed_old_install()
        old = self.hooks_json.read_text()
        self.assertIn("hooks/ai-config", old)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        cmds = self.all_commands(self.hooks_json)
        self.assertFalse([c for c in cmds if "hooks/ai-config/" in c], cmds)
        self.assert_no_duplicates(self.hooks_json)
        self.assertTrue(any("$HOME/.cursor/hooks/brainrc/" in c for c in cmds))
        self.assertIn(USER_CURSOR_HOOK, cmds)
        self.assert_second_apply_is_a_no_op()


class InstalledOldLinkTest(OldInstallCase):
    """Installed mode: core hooks come from a copy in the resolved home."""

    def setUp(self):
        super().setUp()
        self.pkg = Path(tempfile.mkdtemp()) / "brainrc"
        self.core = self.pkg / "_core"
        shutil.copytree(self.repo, self.core, symlinks=True)
        roles = self.core / "skills/spec-agent/roles"
        roles.unlink()
        shutil.copytree(self.core / "agents", roles)
        brainrc.config.REPO = self.core

    def tearDown(self):
        shutil.rmtree(self.pkg.parent)
        super().tearDown()

    def test_old_link_to_the_resolved_homes_copy_is_pruned_and_the_copy_used(self):
        copy = self.settings_home / "hooks/core/claude/hooks"
        copy.mkdir(parents=True)
        for src in (self.core / "overrides/claude/hooks").iterdir():
            if src.is_file():
                shutil.copy2(src, copy / src.name)
        hooks = self.home / ".claude/hooks"
        hooks.mkdir(parents=True)
        (hooks / "ai-config").symlink_to(copy)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((hooks / "ai-config").is_symlink())
        self.assertTrue(copy.is_dir())
        self.assertEqual(brainrc.link_target(hooks / "brainrc"), copy)
        self.assertTrue((copy / "guard_outward.py").is_file())
        self.assertEqual(sorted(p.name for p in hooks.iterdir()), ["brainrc"])
        self.assertEqual(quiet(brainrc.cmd_sync, False)[1].strip(), "Everything in sync.")
