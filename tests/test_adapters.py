"""The adapter interface (#306): each shipped tool has an adapter, and a Python package can add a
tool through the `brainrc.adapters` entry point group without a change to core."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import home_env, restore_home, rmtree, saved_home  # noqa: E402
from test_brainrc import TempRepoCase, brainrc, install_harnesses, quiet  # noqa: E402

from brainrc import adapters, capabilities, config  # noqa: E402
from brainrc.config import ConfigError  # noqa: E402

ADAPTER_MODULE = '''
from brainrc.adapters import Adapter


class AcmeTool(Adapter):
    name = "acmetool"
    label = "Acme Tool"
    paths = {"skills": "~/.acmetool/skills", "instructions": "~/.acmetool/AGENTS.md"}


class Misnamed(Adapter):
    name = "other"


NotAnAdapter = object()
'''


class BuiltinTest(unittest.TestCase):
    def test_every_shipped_tool_has_an_adapter_with_a_label(self):
        shipped = config._read_toml(config.REPO / "harnesses.toml")
        self.assertEqual(list(shipped), list(adapters.BUILTIN))
        for name, adapter in adapters.BUILTIN.items():
            self.assertEqual(adapter.name, name)
            self.assertTrue(adapter.label, name)

    def test_a_table_with_no_adapter_reads_content_as_claude_code_writes_it(self):
        mine = adapters.get("mytool")
        self.assertIsInstance(mine, adapters.Plain)
        self.assertEqual((mine.label, adapters.agents_format("mytool", {}), adapters.settings_format("mytool", {})),
                         ("mytool", "claude", "claude"))
        self.assertFalse(mine.writes_mcp)
        self.assertEqual(mine.sandbox, {})

    def test_a_format_key_borrows_another_adapter_s_format(self):
        self.assertIs(adapters.agent_renderer("mytool", {"agents_format": "opencode"}), adapters.BUILTIN["opencode"])
        self.assertIsNone(adapters.agent_renderer("opencode", {"agents_format": "claude"}))
        self.assertEqual(adapters.settings_format("mytool", {"settings_format": "antigravity"}), "antigravity")
        with self.assertRaisesRegex(ConfigError, r"unknown agents_format `nope` \(use one of claude, opencode\)"):
            adapters.agents_format("opencode", {"agents_format": "nope"})

    def test_the_mcp_writers_and_sandboxes_are_the_adapters_own(self):
        self.assertEqual(brainrc.mcp.writers(),
                         ["claude", "codex", "opencode", "gemini", "copilot", "devin", "kiro", "amp", "junie"])
        self.assertEqual([n for n, a in adapters.BUILTIN.items() if a.sandbox], ["claude"])
        self.assertEqual(capabilities.LABELS["antigravity"], "Antigravity CLI")


class E31ToolsTest(TempRepoCase):
    """The tools E31 adds (#307 to #312) next to files the user already has."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        super().tearDown()

    def sync(self) -> None:
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)

    def test_kiro_keeps_the_user_s_own_hook_entries_as_they_are(self):
        mine = {"name": "lint", "trigger": "PostToolUse", "matcher": "fs_write",
                "action": {"type": "agent", "prompt": "Lint it."}, "enabled": False}
        hooks = self.home / ".kiro/hooks/brainrc.json"
        hooks.parent.mkdir(parents=True)
        hooks.write_text(json.dumps({"version": "v1", "hooks": [mine]}))
        self.sync()
        data = json.loads(hooks.read_text())
        self.assertEqual(data["hooks"][0], mine)
        self.assertEqual([(e["trigger"], e["matcher"]) for e in data["hooks"][1:]], [("PreToolUse", "*")])
        self.assertIn("/.kiro/hooks/brainrc/guard.py", data["hooks"][1]["action"]["command"])
        (self.repo / "harnesses.local.toml").write_text("[kiro]\nenabled = false\n")
        self.sync()
        self.assertEqual(json.loads(hooks.read_text()), {"version": "v1", "hooks": [mine]})

    def test_kiro_hooks_that_are_not_a_list_are_left_alone(self):
        hooks = self.home / ".kiro/hooks/brainrc.json"
        hooks.parent.mkdir(parents=True)
        hooks.write_text('{"hooks": {"PreToolUse": []}}')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertIn("its `hooks` isn't a list of hook objects", out)
        self.assertEqual(hooks.read_text(), '{"hooks": {"PreToolUse": []}}')

    def test_amp_writes_into_settings_jsonc_when_only_it_exists_and_keeps_its_comments(self):
        (self.repo / "mcp").mkdir(exist_ok=True)
        (self.repo / "mcp/servers.toml").write_text('[servers.acme-search]\nurl = "https://search.acme.example/mcp"\n')
        jsonc = self.home / ".config/amp/settings.jsonc"
        jsonc.write_text('{\n  // my theme\n  "amp.theme": "dark"\n}\n')
        self.sync()
        text = jsonc.read_text()
        self.assertIn("// my theme", text)
        self.assertIn('"amp.mcpServers"', text)
        self.assertFalse((self.home / ".config/amp/settings.json").exists())

    def test_devin_and_junie_spell_an_env_variable_their_own_way(self):
        server = {"command": "acme-docs-mcp", "env_from": ["ACME_DOCS_TOKEN"]}
        self.assertEqual(adapters.get("devin").mcp_entry(server)["env"], {"ACME_DOCS_TOKEN": "${env:ACME_DOCS_TOKEN}"})
        self.assertNotIn("env", adapters.get("junie").mcp_entry(server))  # Junie reads no references
        self.assertEqual(adapters.get("gemini").mcp_entry({"url": "https://x.example/mcp"}),
                         {"httpUrl": "https://x.example/mcp"})


class EntryPointTest(TempRepoCase):
    """An installed package's adapter, through a real dist-info on sys.path."""

    def setUp(self):
        super().setUp()
        self.site = Path(tempfile.mkdtemp()).resolve()
        (self.site / "acme_tool.py").write_text(ADAPTER_MODULE)
        self.points("acmetool = acme_tool:AcmeTool")
        sys.path.insert(0, str(self.site))
        adapters.reset()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)

    def tearDown(self):
        sys.path.remove(str(self.site))
        sys.modules.pop("acme_tool", None)
        adapters.reset()
        restore_home(self.old_home)
        rmtree(self.home)
        rmtree(self.site)
        super().tearDown()

    def points(self, *lines: str) -> None:
        info = self.site / "acme_tool-1.0.dist-info"
        info.mkdir(exist_ok=True)
        (info / "METADATA").write_text("Metadata-Version: 2.1\nName: acme-tool\nVersion: 1.0\n")
        (info / "entry_points.txt").write_text("[brainrc.adapters]\n" + "\n".join(lines) + "\n")
        adapters.reset()

    def test_the_adapter_brings_its_tool_and_paths(self):
        self.assertEqual(adapters.get("acmetool").label, "Acme Tool")
        every = config.load_harnesses(include_disabled=True)
        self.assertEqual(every["acmetool"], {"skills": "~/.acmetool/skills", "instructions": "~/.acmetool/AGENTS.md"})
        self.assertNotIn("acmetool", config.load_harnesses())  # not installed here: skipped, as any tool

    def test_apply_writes_its_files_once_the_tool_is_installed(self):
        (self.home / ".acmetool").mkdir()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.home / ".acmetool/skills/brainrc-work").is_symlink())
        self.assertEqual(brainrc.link_target(self.home / ".acmetool/AGENTS.md"), brainrc.rendered_instructions())

    def test_harnesses_local_toml_moves_its_paths_and_turns_it_off(self):
        (self.home / ".acmetool").mkdir()
        (self.repo / "harnesses.local.toml").write_text('[acmetool]\nskills = "~/elsewhere/skills"\n')
        self.assertEqual(config.load_harnesses()["acmetool"]["skills"], "~/elsewhere/skills")
        self.assertEqual(brainrc.config.check_config(), [])  # a known table, not the user's own
        (self.repo / "harnesses.local.toml").write_text("[acmetool]\nenabled = false\n")
        self.assertNotIn("acmetool", config.load_harnesses())

    def test_a_shipped_tool_s_name_stays_the_shipped_adapter(self):
        self.points("codex = acme_tool:AcmeTool")
        self.assertIs(adapters.get("codex"), adapters.BUILTIN["codex"])
        self.assertNotIn("codex", adapters.plugins())

    def test_a_broken_entry_point_names_itself(self):
        for line, why in (("acmetool = acme_tool:Missing", "can't load it"),
                          ("acmetool = acme_tool:NotAnAdapter", "isn't a brainrc.adapters.Adapter"),
                          ("acmetool = acme_tool:Misnamed", "names itself `other`")):
            self.points(line)
            with self.assertRaisesRegex(ConfigError, rf"adapter `acmetool` \(acme_tool:\w+\).*{why}"):
                adapters.plugins()

    def test_a_bad_paths_value_is_a_config_error(self):
        (self.site / "acme_tool.py").write_text(ADAPTER_MODULE.replace(
            '"instructions": "~/.acmetool/AGENTS.md"', '"enabled": "yes"'))
        sys.modules.pop("acme_tool", None)
        adapters.reset()
        with self.assertRaisesRegex(ConfigError, r"adapter `acmetool`: `enabled` in its paths must be true or false"):
            config.load_harnesses()


if __name__ == "__main__":
    unittest.main()
