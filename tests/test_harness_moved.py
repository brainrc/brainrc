"""Review fixes for #110: a harness whose env var changed between applies, the manifest trust
check per harness, OpenCode's two MCP files, and comments kept by the JSONC edit."""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import brainrc, quiet  # noqa: E402
from test_harness_env import HarnessEnvCase  # noqa: E402
from test_uninstall import run  # noqa: E402

from brainrc import config, jsonc  # noqa: E402
from brainrc.manifest import checked_manifest, manifest_file  # noqa: E402
from brainrc.mcp import McpSync, mcp_change, mcp_file  # noqa: E402


class MovedTest(HarnessEnvCase):
    def setUp(self):
        super().setUp()
        self.default = self.home / ".claude"
        self.other = self.elsewhere / "claude"
        self.default.mkdir()
        self.other.mkdir()

    def apply(self, value):
        self.configure("claude", value)
        code, out = run("apply", "--only", "claude")
        self.assertEqual(code, 0, out)
        return out

    def brainrc_left_in(self, d: Path) -> bool:
        settings = d / "settings.json"
        return (d / "skills" / "spec-agent").is_symlink() or (settings.is_file() and "brainrc" in settings.read_text())

    def test_default_then_var_warns_and_uninstall_cleans_both(self):
        self.apply(None)
        out = self.apply(str(self.other))
        self.assertIn(f"WARN claude's config dir moved from ~/.claude to {self.other.as_posix()}", out)
        self.assertIn("removes them with the rest", out)
        code, out = quiet(brainrc.cmd_doctor)
        self.assertRegex(out, r"WARN claude: \d+ of brainrc's links are still in ~/.claude, but claude reads")
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertFalse(self.brainrc_left_in(self.default), out)
        self.assertFalse(self.brainrc_left_in(self.other), out)

    def test_var_then_default_says_how_to_clean_the_old_dir(self):
        self.apply(str(self.other))
        out = self.apply(None)
        self.assertIn(f"WARN claude's config dir moved from {self.other.as_posix()} to ~/.claude", out)
        self.assertIn("run with CLAUDE_CONFIG_DIR set as before", out)
        self.configure("claude", str(self.other))  # the fix the warning gives
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertFalse(self.brainrc_left_in(self.default), out)
        self.assertFalse(self.brainrc_left_in(self.other), out)

    def test_status_warns_before_apply_records_the_move(self):
        self.apply(None)
        self.configure("claude", str(self.other))
        code, out = run("status", "--only", "claude")
        self.assertIn("WARN claude's config dir moved from ~/.claude", out)

    def test_same_dir_twice_is_quiet(self):
        self.apply(str(self.other))
        self.assertNotIn("moved", self.apply(str(self.other)))
        code, out = quiet(brainrc.cmd_doctor)
        self.assertNotIn("still in", out)


class TrustTest(HarnessEnvCase):
    def write(self, **paths):
        manifest_file().parent.mkdir(parents=True, exist_ok=True)
        manifest_file().write_text(json.dumps({"version": 1, "roots": [], "harnesses": {"claude": paths}}))

    def trusted(self, **env) -> bool:
        for var in config.HARNESS_VARS:
            os.environ.pop(var, None)
        os.environ.update(env)
        return "claude" in checked_manifest()[0]["harnesses"]

    def test_only_the_harness_own_var_widens_it(self):
        etc = self.elsewhere / "etc"
        self.write(home=str(etc / "claude"), skills=str(etc / "claude" / "skills"))
        self.assertFalse(self.trusted())
        self.assertFalse(self.trusted(XDG_CONFIG_HOME=str(etc)))  # opencode's var, not claude's
        self.assertFalse(self.trusted(CODEX_HOME=str(etc)))
        self.assertTrue(self.trusted(CLAUDE_CONFIG_DIR=str(etc)))

    def test_a_var_naming_home_or_above_trusts_nothing_more(self):
        self.write(home=str(self.home), skills=str(self.home))
        for value in (str(self.home), str(self.home.parent), "/"):
            with self.subTest(value=value):
                self.assertFalse(self.trusted(CLAUDE_CONFIG_DIR=value))


class OpencodeTwoFilesTest(HarnessEnvCase):
    def test_servers_stay_in_jsonc_once_json_appears_and_uninstall_finds_them(self):
        d, _ = self.configure("opencode", None)
        jc, js = d / "opencode.jsonc", d / "opencode.json"
        jc.write_text("{\n  // mine\n}\n")
        run("apply", "--only", "opencode")
        js.write_text('{"theme": "dark"}\n')
        self.assertEqual(mcp_file("opencode", {"mcp": str(js)}), jc)
        code, out = run("status", "--only", "opencode")
        self.assertIn("Everything in sync.", out)
        self.assertNotIn("docs", js.read_text())
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertNotIn("docs", jc.read_text())
        self.assertIn("// mine", jc.read_text())
        self.assertEqual(json.loads(js.read_text()), {"theme": "dark"})


DB = ('{\n  "mcp": {\n    // my local db: keep disabled until the VPN is up\n'
      '    "db": {"type": "local", "command": ["db-mcp"], "enabled": false}\n  }\n}\n')


class ServerCommentsTest(HarnessEnvCase):
    def test_comments_on_the_user_servers_survive_apply_and_uninstall(self):
        d, _ = self.configure("opencode", None)
        jc = d / "opencode.jsonc"
        jc.write_text(DB)
        code, out = run("apply", "--only", "opencode")
        self.assertEqual(code, 0, out)
        self.assertIn("// my local db", jc.read_text())
        self.assertEqual(set(jsonc.loads(jc.read_text())["mcp"]), {"db", "docs"})
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertEqual(jc.read_text(), DB)

    def test_an_emptied_mcp_object_with_a_comment_stays(self):
        d, _ = self.configure("opencode", None)
        jc = d / "opencode.jsonc"
        jc.write_text('{\n  "mcp": {\n    // add servers here\n  }\n}\n')
        run("apply", "--only", "opencode")
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertIn("// add servers here", jc.read_text())
        self.assertEqual(jsonc.loads(jc.read_text()), {"mcp": {}})
        self.assertEqual(mcp_change(McpSync("opencode", jc, {}))[0], "ok")  # stable: nothing left to undo


class JsoncCommentsTest(unittest.TestCase):
    def check(self, text, value, want):
        out = jsonc.set_key(text, "mcp", value)
        self.assertEqual(jsonc.loads(out), want)
        for c in jsonc._scan(text)[1]:
            if c[0] != "// gone":
                self.assertIn(c[0], out)
        return out

    def test_insert_into_an_object_of_only_comments(self):
        self.check("{\n  // add providers here later\n}\n", {"z": 1}, {"mcp": {"z": 1}})

    def test_insert_after_a_trailing_comment_keeps_it_on_its_member(self):
        out = self.check('{\n  "a": 1 // about a\n}\n', {"z": 1}, {"a": 1, "mcp": {"z": 1}})
        self.assertIn('"a": 1, // about a\n', out)

    def test_remove_keeps_comments_above_and_on_the_line(self):
        text = '{\n  "a": 1,\n  // why b is 2\n  /* x */ "mcp": {},\n  "b": 2\n}\n'
        self.check(text, None, {"a": 1, "b": 2})
        self.check('{\n  "a": 1,\n  // about mcp\n  "mcp": {"x": 1}\n}\n', None, {"a": 1})

    def test_comments_inside_the_old_value_may_go(self):
        self.check('{\n  "mcp": {"x": 1 // gone\n  }\n}\n', {"y": 2}, {"mcp": {"y": 2}})

    def test_a_nested_key(self):
        out = jsonc.set_key(DB, ("mcp", "x"), {"a": 1})
        self.assertIn("// my local db", out)
        self.assertEqual(jsonc.set_key(out, ("mcp", "x"), None), DB)
        self.assertEqual(jsonc.set_key('{"mcp": {"x": 1}}', ("mcp", "y"), 2), '{"mcp": {"x": 1,\n  "y": 2\n}}')

    def test_no_space_left_after_a_comment(self):
        out = jsonc.set_key('{\n  "a": 1,\n  /* x */ "mcp": {},\n  "b": 2\n}\n', "mcp", None)
        self.assertIn("/* x */\n", out)

    def test_same_line_members(self):
        self.assertEqual(jsonc.set_key('{"a": 1, "mcp": {}, "b": 2}', "mcp", None), '{"a": 1, "b": 2}')


if __name__ == "__main__":
    unittest.main()
