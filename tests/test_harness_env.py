"""Each harness's own env var moves its paths (#110): CLAUDE_CONFIG_DIR (#132), CODEX_HOME (#133)
and XDG_CONFIG_HOME for OpenCode (#134). Set, they win; unset, empty or relative, the default does."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet  # noqa: E402
from test_uninstall import run  # noqa: E402

from brainrc import config, jsonc  # noqa: E402
from brainrc.mcp import McpSync, mcp_change, mcp_file  # noqa: E402
from support import home_env, rmtree  # noqa: E402

# harness -> (env var, its default dir under ~, the dir under the var, MCP file relative to ~ / the var)
HARNESSES = {
    "claude": ("CLAUDE_CONFIG_DIR", ".claude", "", ".claude.json", ".claude.json"),
    "codex": ("CODEX_HOME", ".codex", "", ".codex/config.toml", "config.toml"),
    "opencode": ("XDG_CONFIG_HOME", ".config/opencode", "opencode", ".config/opencode/opencode.json",
                 "opencode/opencode.json"),
}


class EnvDirTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        patcher = mock.patch.dict(os.environ, home_env(self.home))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(rmtree, self.home)
        for var in config.HARNESS_VARS:
            os.environ.pop(var, None)

    def test_set_to_an_absolute_path_wins(self):
        os.environ["CODEX_HOME"] = "/opt/codex/"
        self.assertEqual(config.env_default("${CODEX_HOME:-~/.codex}/skills"), "/opt/codex/skills")

    def test_a_path_under_home_is_written_with_a_tilde(self):
        os.environ["CLAUDE_CONFIG_DIR"] = os.path.join(self.home, "alt", "claude")
        self.assertEqual(config.env_default("${CLAUDE_CONFIG_DIR:-~/.claude}/skills"), "~/alt/claude/skills")
        os.environ["CLAUDE_CONFIG_DIR"] = "~/alt2"
        self.assertEqual(config.env_dir("CLAUDE_CONFIG_DIR", "~/.claude"), "~/alt2")

    def test_unset_empty_or_relative_falls_back(self):
        for value in (None, "", "relative/dir"):
            with self.subTest(value=value):
                if value is not None:
                    os.environ["XDG_CONFIG_HOME"] = value
                self.assertEqual(config.env_default("${XDG_CONFIG_HOME:-~/.config}/opencode"), "~/.config/opencode")

    def test_paths_without_the_syntax_are_unchanged(self):
        self.assertEqual(config.env_default("~/.cursor/skills"), "~/.cursor/skills")
        self.assertEqual(config.env_default("$HOME/x"), "$HOME/x")

    def test_claude_dir(self):
        self.assertEqual(config.claude_dir(), Path(self.home) / ".claude")
        os.environ["CLAUDE_CONFIG_DIR"] = "/opt/claude"
        self.assertEqual(config.claude_dir(), Path("/opt/claude"))


class HarnessEnvCase(TempRepoCase):
    """A fresh HOME, with the harness under test installed where its env var (or the default) says."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.elsewhere = Path(tempfile.mkdtemp()).resolve()  # outside HOME
        patcher = mock.patch.dict(os.environ, home_env(self.home))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(rmtree, self.home)
        self.addCleanup(rmtree, self.elsewhere)
        (self.repo / "mcp").mkdir(exist_ok=True)
        (self.repo / "mcp/servers.toml").write_text('[servers.docs]\nurl = "https://example.com/mcp"\n')

    def configure(self, harness: str, value: str | None) -> tuple[Path, Path]:
        """Set (or unset) the harness's var; install the harness where it now lives. Returns
        (harness dir, MCP file)."""
        var, default, sub, mcp_default, mcp_under = HARNESSES[harness]
        if value is None:
            os.environ.pop(var, None)
        else:
            os.environ[var] = value
        if value and os.path.isabs(value):
            root = Path(value)
            d, mcp = root / sub if sub else root, root / mcp_under
        else:
            d, mcp = self.home / default, self.home / mcp_default
        d.mkdir(parents=True, exist_ok=True)
        return d, mcp

    def lifecycle(self, harness: str, value: str | None, doctor_warns: str = "") -> tuple[Path, Path]:
        """status, apply, status, doctor, uninstall for one harness; asserts each used d, and that
        doctor found nothing (or only the warning given)."""
        d, mcp = self.configure(harness, value)
        code, out = run("status", "--only", harness)
        self.assertEqual(code, 0, out)
        self.assertIn(config.tilde(d / "skills"), out)
        code, out = run("apply", "--only", harness)
        self.assertEqual(code, 0, out)
        self.assertTrue((d / "skills" / "spec-agent").is_symlink(), out)
        self.assertTrue(mcp.is_file(), out)
        self.assertIn("docs", mcp.read_text())
        code, out = run("status", "--only", harness)
        self.assertEqual(code, 0, out)
        self.assertIn("Everything in sync.", out)
        code, out = quiet(brainrc.cmd_doctor)
        self.assertEqual(code, 0, out)
        self.assertIn(f"WARN {doctor_warns}\n" if doctor_warns else "No problems found.", out)
        self.assertNotIn("1 warning" if not doctor_warns else "2 warning", out)
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        self.assertNotIn("ignored harness", out)
        self.assertFalse((d / "skills" / "spec-agent").exists())
        self.assertFalse(mcp.is_file() and "docs" in mcp.read_text())
        return d, mcp


class SetTest(HarnessEnvCase):
    def test_claude_config_dir_outside_home(self):
        d, mcp = self.lifecycle("claude", str(self.elsewhere / "claude"))
        self.assertEqual(mcp, d / ".claude.json")
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".claude.json").exists())

    def test_claude_hook_commands_point_into_the_var(self):
        d, _ = self.configure("claude", str(self.elsewhere / "claude"))
        run("apply", "--only", "claude")
        settings = (d / "settings.json").read_text()
        self.assertIn(str(d / "hooks" / "brainrc"), settings)
        self.assertTrue((d / "hooks" / "brainrc").is_symlink())

    def test_codex_home_under_home(self):
        self.lifecycle("codex", str(self.home / "alt" / "codex"))
        self.assertFalse((self.home / ".codex").exists())

    def test_codex_manifest_records_the_resolved_path(self):
        self.configure("codex", str(self.home / "alt" / "codex"))
        run("apply", "--only", "codex")
        manifest = json.loads((self.settings_home / "harnesses.json").read_text())
        self.assertEqual(manifest["harnesses"]["codex"]["skills"], "~/alt/codex/skills")

    def test_opencode_xdg_config_home(self):
        d, mcp = self.lifecycle("opencode", str(self.elsewhere / "xdg"))
        self.assertEqual(d, self.elsewhere / "xdg" / "opencode")
        self.assertFalse((self.home / ".config" / "opencode").exists())


class UnsetTest(HarnessEnvCase):
    def test_each_harness_uses_its_default(self):
        for harness in HARNESSES:
            with self.subTest(harness=harness):
                d, _ = self.lifecycle(harness, None)
                self.assertTrue(str(d).startswith(str(self.home)))
                rmtree(d)  # uninstalled: the next harness's doctor run sees only itself


class EmptyTest(HarnessEnvCase):
    def test_each_harness_uses_its_default(self):
        for harness in HARNESSES:
            with self.subTest(harness=harness):
                d, _ = self.lifecycle(harness, "")
                self.assertEqual(d, self.home / HARNESSES[harness][1])
                rmtree(d)  # uninstalled: the next harness's doctor run sees only itself


class RelativeTest(HarnessEnvCase):
    def test_a_relative_value_is_ignored(self):
        d, _ = self.lifecycle("codex", "rel/codex", "CODEX_HOME is set but not to an absolute path, "
                              "so brainrc ignores it and uses the default dir")
        self.assertEqual(d, self.home / ".codex")


class DoctorPluginDirTest(HarnessEnvCase):
    def test_doctor_reads_claude_plugins_from_the_var(self):
        d, _ = self.configure("claude", str(self.elsewhere / "claude"))
        (d / "plugins").mkdir()
        (d / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"brainrc@brainrc": []}}))
        run("apply", "--only", "claude")
        code, out = quiet(brainrc.cmd_doctor)
        self.assertIn("both the plugin brainrc@brainrc and brainrc's links in " + config.tilde(d), out)
        settings = json.loads((d / "settings.json").read_text())
        (d / "settings.json").write_text(json.dumps({**settings, "enabledPlugins": {"brainrc@brainrc": False}}))
        code, out = quiet(brainrc.cmd_doctor)
        self.assertNotIn("both the plugin", out)  # read from $CLAUDE_CONFIG_DIR/settings.json


JSONC = """{
  // my settings
  "$schema": "https://opencode.ai/config.json",
  "theme": "dark", /* keep me */
  "mcp": {
    "mine": {"type": "local", "command": ["x"]}, // my server
  },
}
"""


class OpencodeJsoncTest(HarnessEnvCase):
    def test_an_existing_jsonc_is_merged_and_keeps_comments(self):
        d, _ = self.configure("opencode", None)
        jc = d / "opencode.jsonc"
        jc.write_text(JSONC)
        code, out = run("apply", "--only", "opencode")
        self.assertEqual(code, 0, out)
        self.assertFalse((d / "opencode.json").exists())
        text = jc.read_text()
        self.assertIn("// my settings", text)
        self.assertIn("/* keep me */", text)
        data = jsonc.loads(text)
        self.assertEqual(set(data["mcp"]), {"mine", "docs"})
        self.assertEqual(data["theme"], "dark")
        code, out = run("status", "--only", "opencode")
        self.assertIn("Everything in sync.", out)
        code, out = run("uninstall")
        self.assertEqual(code, 0, out)
        data = jsonc.loads(jc.read_text())
        self.assertEqual(set(data["mcp"]), {"mine"})
        self.assertIn("// my settings", jc.read_text())

    def test_jsonc_under_xdg(self):
        d, _ = self.configure("opencode", str(self.elsewhere / "xdg"))
        (d / "opencode.jsonc").write_text("{}\n")
        run("apply", "--only", "opencode")
        self.assertIn("docs", jsonc.loads((d / "opencode.jsonc").read_text())["mcp"])
        self.assertFalse((d / "opencode.json").exists())

    def test_json_wins_when_both_exist(self):
        d, _ = self.configure("opencode", None)
        (d / "opencode.json").write_text("{}\n")
        (d / "opencode.jsonc").write_text(JSONC)
        self.assertEqual(mcp_file("opencode", {"mcp": str(d / "opencode.json")}), d / "opencode.json")

    def test_only_opencode_looks_for_jsonc(self):
        (self.home / ".claude.jsonc").write_text("{}")
        self.assertEqual(mcp_file("claude", {"mcp": "~/.claude.json"}), self.home / ".claude.json")

    def test_a_jsonc_it_cant_parse_is_left_alone(self):
        d, _ = self.configure("opencode", None)
        jc = d / "opencode.jsonc"
        jc.write_text('{"mcp": {\n')
        state, *_ = mcp_change(McpSync("opencode", jc, {"docs": {"url": "https://example.com/mcp"}}))
        self.assertEqual(state, "invalid")


class JsoncTest(unittest.TestCase):
    def test_loads_comments_and_trailing_commas(self):
        self.assertEqual(jsonc.loads(JSONC)["mcp"]["mine"]["command"], ["x"])
        self.assertEqual(jsonc.loads('{"a": "// /* not comments */", "b": [1, 2,],}'),
                         {"a": "// /* not comments */", "b": [1, 2]})

    def test_set_replaces_adds_and_removes_one_key(self):
        out = jsonc.set_key(JSONC, "mcp", {"x": {"type": "remote"}})
        self.assertEqual(jsonc.loads(out)["mcp"], {"x": {"type": "remote"}})
        self.assertIn("/* keep me */", out)
        out = jsonc.set_key(out, "mcp", None)
        self.assertNotIn("mcp", jsonc.loads(out))
        self.assertIn("/* keep me */", out)
        out = jsonc.set_key(out, "mcp", {"y": 1})
        self.assertEqual(jsonc.loads(out)["mcp"], {"y": 1})
        for text in ("{}", '{"a": 1}', '{"a": 1,}', '{\n  "mcp": 1\n}', '{"mcp": 1, "b": 2}'):
            with self.subTest(text=text):
                self.assertEqual(jsonc.loads(jsonc.set_key(text, "mcp", {"z": 1}))["mcp"], {"z": 1})
                self.assertNotIn("mcp", jsonc.loads(jsonc.set_key(text, "mcp", None)))

    def test_rejects_what_isnt_an_object(self):
        for text in ("[]", '{"a" 1}', '{"a": 1', "/* open"):
            with self.subTest(text=text), self.assertRaises((ValueError, IndexError)):
                jsonc.set_key(text, "mcp", {"z": 1})


if __name__ == "__main__":
    unittest.main()
