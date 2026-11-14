"""`brainrc audit` (#291): every skill, agent, command, rule, hook and MCP server each harness loads,
with its source, commit and hash, the lock's permissions and the MCP tool pins; `--json` too.
It reads only: no network, nothing written, no absolute home path in the output."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import quiet  # noqa: E402
from test_lock import GitLockCase, rev  # noqa: E402
from test_mcp_pins import PinCase  # noqa: E402

from brainrc import audit, lock, mcp_pins  # noqa: E402
import brainrc  # noqa: E402


def files_under(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class PackAuditTest(PinCase):
    def setUp(self):
        super().setUp()
        quiet(brainrc.cmd_sync, True)

    def audit_json(self) -> dict:
        code, out = quiet(brainrc.main, ["brainrc", "audit", "--json"])
        self.assertEqual(code, 0, out)
        self.assertNotIn(self.home.as_posix(), out)  # ~ instead
        return json.loads(out)

    def entry(self, data: dict, harness: str, kind: str, name: str) -> dict:
        found = [e for e in data["tools"][harness] if e["kind"] == kind and e["name"] == name]
        self.assertEqual(len(found), 1, [(e["kind"], e["name"]) for e in data["tools"][harness]])
        return found[0]

    def test_items_carry_their_source_and_hash(self):
        data = self.audit_json()
        skill = self.entry(data, "claude", "skill", "acme-deploy")
        self.assertEqual((skill["source"], skill["file"], skill["installed"]), ("acme", "acme:skills/acme-deploy", True))
        self.assertEqual(skill["hash"], audit._hash(self.pack / "skills/acme-deploy"))
        self.assertEqual(skill["path"], "~/.claude/skills/acme-deploy")
        agent = self.entry(data, "claude", "agent", "acme-reviewer")
        self.assertEqual(agent["hash"], lock.digest((self.pack / "agents/acme-reviewer.md").read_bytes()))
        rule = self.entry(data, "codex", "rule", "50-acme")
        self.assertEqual((rule["source"], rule["path"]), ("acme", "~/.codex/AGENTS.md"))
        self.assertEqual(self.entry(data, "claude", "rule", "00-core")["source"], "core")

    def test_hooks_servers_permissions_and_pins(self):
        data = self.audit_json()
        hook = self.entry(data, "claude", "hook", "PreToolUse [Bash] guard_acme.py")
        self.assertEqual(hook["hash"], lock.digest((self.pack / "overrides/claude/hooks/guard_acme.py").read_bytes()))
        self.assertTrue(hook["installed"])
        self.entry(data, "claude", "hook", "SessionStart [startup] check_mcp_pins.py")
        server = self.entry(data, "claude", "mcp", "acme-local")
        self.assertEqual((server["source"], server["pin"], server["installed"]), ("acme", "not pinned", True))
        self.assertEqual(server["server"]["command"], Path(sys.executable).as_posix().replace(self.home.as_posix(), "~"))
        self.assertIn("hooks", data["sources"]["acme"]["permissions"])
        self.pin()
        self.assertEqual(self.entry(self.audit_json(), "claude", "mcp", "acme-local")["pin"], "2 tool(s) pinned")

    def test_an_item_apply_has_not_installed_yet_says_so(self):
        (self.pack / "skills/acme-new").mkdir()
        (self.pack / "skills/acme-new/SKILL.md").write_text("---\nname: acme-new\ndescription: New.\n---\nBody.\n")
        self.assertFalse(self.entry(self.audit_json(), "claude", "skill", "acme-new")["installed"])
        code, out = quiet(brainrc.main, ["brainrc", "audit"])
        self.assertIn("acme-new  (not installed: apply)", out)

    def test_it_writes_nothing_and_needs_no_lock(self):
        before = files_under(self.settings_home), files_under(self.home)
        quiet(brainrc.main, ["brainrc", "audit"])
        self.audit_json()
        self.assertEqual((files_under(self.settings_home), files_under(self.home)), before)
        lock.user_lock_path().unlink()
        data = self.audit_json()
        self.assertIsNone(data["lock"])
        self.assertNotIn("permissions", data["sources"]["acme"])

    def test_a_secret_in_the_server_url_is_not_printed(self):
        self.add_servers('[servers.acme-docs]\nurl = "https://user:s3cret@docs.acme.example/mcp"\n')
        code, out = quiet(brainrc.main, ["brainrc", "audit", "--json"])
        self.assertNotIn("s3cret", out)
        self.assertEqual(json.loads(out)["tools"]["claude"][-1]["server"], {"url": "https://docs.acme.example/mcp"})


class GitPackAuditTest(GitLockCase):
    def test_a_git_pack_is_traced_to_its_commit(self):
        self.apply()
        code, out = quiet(brainrc.main, ["brainrc", "audit", "--json"])
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        commit = rev(self.bare, "v1")
        self.assertEqual(data["sources"]["gatework"]["commit"], commit)
        self.assertEqual(data["sources"]["gatework"]["ref"], "v1")
        work = next(e for e in data["tools"]["claude"] if e["name"] == "brainrc-work")
        self.assertEqual((work["source"], work["commit"]), ("gatework", commit))
        code, out = quiet(brainrc.main, ["brainrc", "audit"])
        self.assertIn(f"SOURCE    gatework  {self.url} v1 at {commit[:12]}", out)


class NoServersTest(unittest.TestCase):
    def test_spec_has_no_env_values(self):
        self.assertEqual(mcp_pins.spec({"command": "x", "env_from": ["TOKEN"], "harnesses": ["claude"]}),
                         {"command": "x", "env_from": ["TOKEN"]})


if __name__ == "__main__":
    unittest.main()
