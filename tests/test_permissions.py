"""Permission diff (#289): brainrc.lock records what each pack can do (hooks, MCP servers, tool
grants, network domains); `status` lists what is added or removed against it, and `apply` asks
before any widening unless --yes, refusing when there is no terminal to ask in."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import home_env, restore_home, rmtree, saved_home  # noqa: E402
from test_brainrc import TempRepoCase, install_harnesses, make_pack, quiet, set_core_version  # noqa: E402
from test_project_scope import ProjectCase, make_team_pack  # noqa: E402

from brainrc import lock, permissions, schema  # noqa: E402
import brainrc  # noqa: E402

GUARD = 'claude PreToolUse [Bash] python3 "{{hooks_dir}}/guard_acme.py"'
SERVER = '[servers.acme-docs]\nurl = "https://docs.acme.example/mcp"\n'


class PackPermissionsTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")
        self.enable_pack()
        (self.repo / "brainrc.local.toml").write_text('profile = "full"\n')  # MCP servers too
        self.lock_path = self.settings_home / "brainrc.lock"

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        rmtree(self.pack.parent)
        super().tearDown()

    def enable_pack(self, enabled: bool = True) -> None:
        (self.repo / "packs.local.toml").write_text(
            f"[acme]\npath = '{self.pack.as_posix()}'\nenabled = {str(enabled).lower()}\n")

    def run_sync(self, apply: bool, yes: bool = False, code: int = 0) -> str:
        got, out = quiet(brainrc.cmd_sync, apply, None, False, yes)
        self.assertEqual(got, code, out)
        return out

    def perms(self) -> dict:
        return lock.read(self.lock_path)["packs"]["acme"]["permissions"]

    def add_server(self) -> None:
        (self.pack / "mcp").mkdir(exist_ok=True)
        (self.pack / "mcp/servers.toml").write_text(SERVER)

    def test_the_first_lock_lists_and_records_them_without_asking(self):
        out = self.run_sync(True)
        self.assertIn(f"PERMS     acme      hook     {GUARD}  (first lock: recorded as the baseline)", out)
        self.assertEqual(self.perms(), {"hooks": [GUARD],
                                        "tools": ["agent acme-reviewer: Read", "agent acme-reviewer: mcp__docs__search"]})
        self.assertEqual(schema.errors(lock.read(self.lock_path), schema.load("brainrc.lock")), [])
        self.assertNotIn("PERMS", self.run_sync(True))
        self.assertIn("Everything in sync.", self.run_sync(False))

    def test_status_lists_an_added_server_and_its_domain(self):
        self.run_sync(True)
        self.add_server()
        out = self.run_sync(False)
        self.assertIn("PERMS     acme      + mcp    acme-docs https://docs.acme.example/mcp", out)
        self.assertIn("PERMS     acme      + domain docs.acme.example", out)
        self.assertNotIn("Everything in sync.", out)

    def test_apply_without_a_terminal_refuses_to_widen_and_writes_nothing(self):
        self.run_sync(True)
        before = self.lock_path.read_bytes()
        self.add_server()
        claude_json = self.home / ".claude.json"
        mcp_before = claude_json.read_bytes() if claude_json.exists() else None
        out = self.run_sync(True, code=1)
        self.assertIn("Re-run with --yes to accept them.", out)
        self.assertEqual(self.lock_path.read_bytes(), before)
        self.assertEqual(claude_json.read_bytes() if claude_json.exists() else None, mcp_before)
        self.run_sync(True, yes=True)
        self.assertEqual(self.perms()["mcp"], ["acme-docs https://docs.acme.example/mcp"])
        self.assertIn("acme-docs", json.loads(claude_json.read_text())["mcpServers"])

    def test_a_terminal_yes_applies_and_a_no_writes_nothing(self):
        self.run_sync(True)
        before = self.lock_path.read_bytes()
        self.add_server()
        tty = mock.patch.object(permissions, "interactive", return_value=True)
        with tty, mock.patch("builtins.input", return_value="n") as asked:
            self.run_sync(True, code=1)
        asked.assert_called_once()
        self.assertEqual(self.lock_path.read_bytes(), before)
        with tty, mock.patch("builtins.input", return_value="y"):
            self.run_sync(True)
        self.assertIn("mcp", self.perms())

    def test_a_narrowing_applies_without_asking(self):
        self.run_sync(True)
        (self.pack / "overrides/claude/settings.fragment.json").write_text("{}")
        out = self.run_sync(True)
        self.assertIn(f"PERMS     acme      - hook   {GUARD}", out)
        self.assertNotIn("hooks", self.perms())

    def test_a_new_tool_grant_is_a_widening(self):
        self.run_sync(True)
        agent = self.pack / "agents/acme-reviewer.md"
        agent.write_text(agent.read_text().replace("tools: Read, mcp__docs__search", "tools: Read, Bash"))
        out = self.run_sync(True, code=1)
        self.assertIn("PERMS     acme      + tool   agent acme-reviewer: Bash", out)
        self.assertIn("PERMS     acme      - tool   agent acme-reviewer: mcp__docs__search", out)

    def test_an_agent_without_tools_gets_every_tool(self):
        self.run_sync(True)
        agent = self.pack / "agents/acme-reviewer.md"
        agent.write_text(agent.read_text().replace("tools: Read, mcp__docs__search\n", ""))
        out = self.run_sync(False)
        self.assertIn("PERMS     acme      + tool   agent acme-reviewer: (every tool)", out)

    def test_settings_grants_and_their_domains(self):
        self.run_sync(True)
        fragment = {"permissions": {"allow": ["WebFetch(domain:api.acme.example)"]}}
        (self.pack / "overrides/claude/settings.fragment.json").write_text(json.dumps(fragment))
        out = self.run_sync(False)
        self.assertIn("PERMS     acme      + tool   claude allow WebFetch(domain:api.acme.example)", out)
        self.assertIn("PERMS     acme      + domain api.acme.example", out)

    def test_a_pack_added_to_an_existing_lock_asks(self):
        self.enable_pack(False)
        self.run_sync(True)
        self.enable_pack(True)
        out = self.run_sync(True, code=1)
        self.assertIn(f"PERMS     acme      + hook   {GUARD}", out)
        self.assertNotIn("acme", lock.read(self.lock_path).get("packs", {}))

    def test_a_lock_from_before_permissions_vouches_only_for_unchanged_files(self):
        self.run_sync(True)
        data = lock.read(self.lock_path)
        del data["packs"]["acme"]["permissions"]
        lock.write(self.lock_path, data)
        self.assertNotIn("PERMS", self.run_sync(False))  # same files: the same permissions
        self.run_sync(True)
        self.assertIn("hooks", self.perms())  # and now recorded
        data = lock.read(self.lock_path)
        del data["packs"]["acme"]["permissions"]
        lock.write(self.lock_path, data)
        skill = self.pack / "skills/acme-deploy/SKILL.md"
        skill.write_text(skill.read_text() + "Changed.\n")
        out = self.run_sync(True, code=1)  # changed since: nothing vouches for them
        self.assertIn(f"PERMS     acme      + hook   {GUARD}", out)

    def test_check_catches_a_lock_whose_permissions_were_edited(self):
        self.run_sync(True)
        data = lock.read(self.lock_path)
        data["packs"]["acme"]["permissions"]["hooks"] = []
        lock.write(self.lock_path, data)
        code, out = quiet(brainrc.cli.cmd_check, "user")
        self.assertEqual(code, 1, out)
        self.assertIn("DRIFT pack acme: its permissions differ from what brainrc.lock records", out)

    def test_update_asks_too(self):
        self.run_sync(True)
        self.add_server()
        code, out = quiet(brainrc.cmd_update, [], False)
        self.assertEqual(code, 1, out)
        code, out = quiet(brainrc.cmd_update, [], True)
        self.assertEqual(code, 0, out)


class ProjectPermissionsTest(ProjectCase):
    def test_a_skill_that_pre_approves_tools_is_a_widening_in_the_project(self):
        pack = make_team_pack(self.proj / "tools/team-pack")
        self.manifest('[packs.team]\npath = "tools/team-pack"\n\n[packs.gatework]\nenabled = false\n')
        self.apply()
        skill = pack / "skills/team-deploy/SKILL.md"
        skill.write_text(skill.read_text().replace("description:", "allowed-tools: Bash(kubectl apply:*)\ndescription:"))
        out = self.status()
        self.assertIn("PERMS     team      + tool   skill team-deploy: Bash(kubectl apply:*)", out)
        got, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(got, 1, out)
        self.assertIn("Nothing written in the project.", out)
        self.assertNotIn("allowed-tools", (self.proj / ".agents/skills/team-deploy/SKILL.md").read_text())
        got, out = quiet(brainrc.cmd_sync, True, None, False, True)
        self.assertEqual(got, 0, out)
        team = lock.read(self.proj / "brainrc.lock")["packs"]["team"]
        self.assertEqual(team["permissions"], {"tools": ["skill team-deploy: Bash(kubectl apply:*)"]})


class LockFormatTest(unittest.TestCase):
    def test_permissions_are_sorted_arrays_one_per_line(self):
        data = lock.new_lock("user", {"acme": {"path": "~/acme", "files": {},
                                               "permissions": {"tools": ["b", "a"], "domains": ["x.example"]}}})
        text = lock.dumps(data)
        self.assertIn('[packs.acme.permissions]\ndomains = [\n  "x.example",\n]\ntools = [\n  "a",\n  "b",\n]\n', text)
        self.assertEqual(lock.loads(text)["packs"]["acme"]["permissions"], {"domains": ["x.example"], "tools": ["a", "b"]})


class CliTest(unittest.TestCase):
    def test_frozen_install_takes_no_yes(self):
        code = brainrc.main(["brainrc", "install", "--frozen", "--yes"])
        self.assertEqual(code, 2)

    def test_no_switch_but_the_flag_skips_the_question(self):
        self.assertFalse(permissions.ASSUME_YES)


if __name__ == "__main__":
    unittest.main()
