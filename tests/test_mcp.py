"""Tests for the MCP registry sync: mcp/servers.toml rendered into each harness's MCP config."""
import json
import os
import shutil
import stat
import tempfile
import unittest
import tomllib
from pathlib import Path
from unittest import mock

from test_aicfg import TempRepoCase, aicfg, make_pack, quiet, set_core_version

GH = '[servers.gh]\ncommand = "npx"\nargs = ["-y", "@modelcontextprotocol/server-github"]\nenv_from = ["GH_TOKEN"]\n'
DOCS = '[servers.docs]\nurl = "https://docs.example.com/mcp"\n'
SECRET = "s3cret-value-never-written"


class McpCase(TempRepoCase):
    """A temp repo plus a fake HOME with each harness's directory present."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        os.environ["GH_TOKEN"] = SECRET
        for d in (".claude", ".codex", ".config/opencode", ".gemini/config", ".cursor"):
            (self.home / d).mkdir(parents=True)
        self.claude = self.home / ".claude.json"
        self.codex = self.home / ".codex/config.toml"
        self.opencode = self.home / ".config/opencode/opencode.json"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        os.environ.pop("GH_TOKEN", None)
        shutil.rmtree(self.home)
        super().tearDown()

    def registry(self, text: str, root: Path | None = None) -> None:
        path = (root or self.repo) / "mcp/servers.toml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)

    def apply(self) -> str:
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        return out

    def validate_errors(self) -> str:
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1, out)
        return out


class RegistryTest(McpCase):
    def test_valid_registry_passes(self):
        self.registry(GH + DOCS + '\n[servers.only-codex]\ncommand = "x"\nharnesses = ["codex"]\n')
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_bad_entries_are_reported(self):
        self.registry('[servers.both]\ncommand = "x"\nurl = "https://x"\n'
                      '[servers.neither]\nargs = ["x"]\n'
                      '[servers.secret]\ncommand = "x"\nenv = { TOKEN = "abc" }\n'
                      '[servers.typo]\ncommand = "x"\nenv_form = ["X"]\n'
                      '[servers.badenv]\ncommand = "x"\nenv_from = ["NOT-A-NAME"]\n'
                      '[servers.badharness]\ncommand = "x"\nharnesses = ["vim"]\n'
                      '[servers."has space"]\ncommand = "x"\n')
        out = self.validate_errors()
        for name in ("both", "neither", "secret", "typo", "badenv", "badharness", "has space"):
            self.assertIn(f"mcp/servers.toml: server `{name}`", out)
        self.assertIn("env_from", out)  # the fix for an `env` table names env_from

    def test_mcp_key_needs_an_adapter(self):
        (self.repo / "harnesses.local.toml").write_text('[cursor]\nmcp = "~/.cursor/mcp.json"\n')
        self.assertIn("[cursor] sets `mcp`", self.validate_errors())


class PackServersTest(McpCase):
    def setUp(self):
        super().setUp()
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")
        (self.repo / "packs.local.toml").write_text(f'[acme]\npath = "{self.pack}"\n')

    def tearDown(self):
        shutil.rmtree(self.pack.parent)
        super().tearDown()

    def test_pack_servers_need_the_prefix_and_unique_names(self):
        self.registry('[servers.acme-docs]\nurl = "https://x"\n')
        self.registry('[servers.docs]\nurl = "https://y"\n[servers.acme-docs]\nurl = "https://z"\n', self.pack)
        out = self.validate_errors()
        self.assertIn("server `docs`: must start with the pack prefix `acme-`", out)
        self.assertIn("server `acme-docs`: also defined in", out)

    def test_pack_servers_are_synced(self):
        self.registry('[servers.acme-docs]\nurl = "https://docs.acme.example/mcp"\n', self.pack)
        self.apply()
        self.assertEqual(json.loads(self.claude.read_text())["mcpServers"]["acme-docs"],
                         {"type": "http", "url": "https://docs.acme.example/mcp"})


class AdapterTest(McpCase):
    def servers(self, text: str) -> dict:
        self.registry(text)
        return aicfg.mcp.load_servers(aicfg.sources())

    def test_claude_entries(self):
        s = self.servers(GH + DOCS)
        self.assertEqual(aicfg.mcp.render_entry("claude", s["gh"]),
                         {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                          "env": {"GH_TOKEN": "${GH_TOKEN}"}})
        self.assertEqual(aicfg.mcp.render_entry("claude", s["docs"]),
                         {"type": "http", "url": "https://docs.example.com/mcp"})

    def test_opencode_entries(self):
        s = self.servers(GH + DOCS)
        self.assertEqual(aicfg.mcp.render_entry("opencode", s["gh"]),
                         {"type": "local", "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
                          "environment": {"GH_TOKEN": "{env:GH_TOKEN}"}, "enabled": True})
        self.assertEqual(aicfg.mcp.render_entry("opencode", s["docs"]),
                         {"type": "remote", "url": "https://docs.example.com/mcp", "enabled": True})

    def test_codex_block_round_trips(self):
        s = self.servers(GH + DOCS + '[servers.odd]\ncommand = "a \\"b\\" \\\\ c"\nargs = ["é", "\\n"]\n')
        parsed = tomllib.loads(aicfg.mcp.render_codex_block(s))["mcp_servers"]
        self.assertEqual(parsed["gh"], {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
                                        "env_vars": ["GH_TOKEN"]})
        self.assertEqual(parsed["docs"], {"url": "https://docs.example.com/mcp"})
        self.assertEqual(parsed["odd"], {"command": 'a "b" \\ c', "args": ["é", "\n"]})


class McpSyncTest(McpCase):
    def written(self) -> str:
        return "".join(p.read_text() for p in (self.claude, self.codex, self.opencode) if p.exists())

    def test_empty_registry_writes_nothing(self):
        self.registry("# nothing yet\n")
        self.apply()
        self.assertFalse(self.claude.exists() or self.codex.exists() or self.opencode.exists())

    def test_apply_writes_every_harness_and_never_a_value(self):
        self.registry(GH + DOCS)
        out = self.apply()
        self.assertIn("(mcp)", out)
        self.assertEqual(set(json.loads(self.claude.read_text())["mcpServers"]), {"gh", "docs"})
        self.assertEqual(set(json.loads(self.opencode.read_text())["mcp"]), {"gh", "docs"})
        self.assertEqual(set(tomllib.loads(self.codex.read_text())["mcp_servers"]), {"gh", "docs"})
        self.assertNotIn(SECRET, self.written())
        self.assertIn("Everything in sync", quiet(aicfg.cmd_sync, False)[1])

    def test_foreign_entries_and_keys_are_kept_and_stale_owned_ones_removed(self):
        self.claude.write_text(json.dumps({"userID": "u", "mcpServers": {"mine": {"type": "http", "url": "https://m"}}}))
        self.registry(GH + DOCS)
        self.apply()
        self.registry(GH)
        self.apply()
        data = json.loads(self.claude.read_text())
        self.assertEqual(data["userID"], "u")
        self.assertEqual(set(data["mcpServers"]), {"mine", "gh"})

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_a_private_claude_json_stays_private(self):
        self.claude.write_text(json.dumps({"userID": "u"}))
        self.claude.chmod(0o600)
        self.registry(GH)
        self.apply()
        self.assertIn("gh", json.loads(self.claude.read_text())["mcpServers"])
        self.assertEqual(stat.S_IMODE(self.claude.stat().st_mode), 0o600)

    def test_a_symlinked_claude_json_stays_linked(self):
        dotfiles = self.home / "dotfiles"
        dotfiles.mkdir()
        target = dotfiles / "claude.json"
        target.write_text(json.dumps({"userID": "u"}))
        target.chmod(0o600)
        self.claude.symlink_to(target)
        self.registry(GH)
        self.apply()
        self.assertTrue(self.claude.is_symlink())
        self.assertEqual(self.claude.readlink(), target)
        data = json.loads(target.read_text())
        self.assertEqual(data["userID"], "u")
        self.assertIn("gh", data["mcpServers"])
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)

    def test_a_claude_json_changed_during_apply_is_left_alone(self):
        self.claude.write_text(json.dumps({"userID": "u"}))
        self.registry(GH)
        real = aicfg.cli.mcp_change

        def claude_writes_meanwhile(s):
            result = real(s)
            if s.dest == self.claude:
                self.claude.write_text(json.dumps({"userID": "u", "numStartups": 2}))
            return result

        with mock.patch("aicfg.cli.mcp_change", claude_writes_meanwhile):
            code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"CHANGED +claude +~/.claude.json")
        self.assertIn("close Claude Code", out)
        self.assertEqual(json.loads(self.claude.read_text()), {"userID": "u", "numStartups": 2})
        self.assertIn("gh", json.loads(self.opencode.read_text())["mcp"])

    def test_a_users_own_server_of_the_same_name_is_never_overwritten(self):
        self.claude.write_text(json.dumps({"mcpServers": {"gh": {"type": "stdio", "command": "my-gh"}}}))
        self.registry(GH + DOCS)
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("CONFLICT", out)
        self.assertIn("gh", out)
        servers = json.loads(self.claude.read_text())["mcpServers"]
        self.assertEqual(servers["gh"], {"type": "stdio", "command": "my-gh"})
        self.assertIn("docs", servers)
        self.assertTrue(any("gh" in f[1] and "mcp" in f[1].lower() for f in aicfg.doctor_findings()))

    def test_an_identical_entry_is_adopted_when_ownership_was_lost(self):
        self.registry(GH)
        self.apply()
        (aicfg.aicfg_home() / "mcp-owned.json").unlink()
        self.assertIn("Everything in sync", quiet(aicfg.cmd_sync, False)[1])

    def test_codex_block_keeps_user_content_and_is_removed_cleanly(self):
        original = 'model = "o3"\n\n[mcp_servers.mine]\ncommand = "mine"\n'
        self.codex.write_text(original)
        self.registry(GH)
        self.apply()
        parsed = tomllib.loads(self.codex.read_text())
        self.assertEqual(parsed["model"], "o3")
        self.assertEqual(set(parsed["mcp_servers"]), {"mine", "gh"})
        self.registry("")
        self.apply()
        self.assertEqual(self.codex.read_text(), original)

    def test_harnesses_filter(self):
        self.registry(GH + 'harnesses = ["codex"]\n')
        self.apply()
        self.assertFalse(self.claude.exists())
        self.assertIn("gh", tomllib.loads(self.codex.read_text())["mcp_servers"])

    def test_disabling_a_harness_removes_its_servers(self):
        self.registry(GH)
        self.apply()
        (self.repo / "harnesses.local.toml").write_text("[opencode]\nenabled = false\n")
        self.apply()
        self.assertEqual(json.loads(self.opencode.read_text()).get("mcp", {}), {})

    def test_doctor_reports_drift_until_apply(self):
        self.registry(GH)
        self.apply()
        self.registry(GH + DOCS)
        self.assertTrue(any("mcp" in f[1].lower() for f in aicfg.doctor_findings()))
        self.apply()
        self.assertEqual([f for f in aicfg.doctor_findings() if "mcp" in f[1].lower()], [])
