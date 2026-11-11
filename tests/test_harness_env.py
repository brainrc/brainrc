"""Each harness's own env var moves its paths (#110): CLAUDE_CONFIG_DIR (#132). Set, they win; unset, empty or relative, the default does."""
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

from brainrc import config  # noqa: E402

# harness -> (env var, its default dir under ~, the dir under the var, MCP file relative to ~ / the var)
HARNESSES = {
    "claude": ("CLAUDE_CONFIG_DIR", ".claude", "", ".claude.json", ".claude.json"),
}


class EnvDirTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        patcher = mock.patch.dict(os.environ, {"HOME": self.home})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.home)
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
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.home)
        self.addCleanup(shutil.rmtree, self.elsewhere)
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

    def lifecycle(self, harness: str, value: str | None) -> tuple[Path, Path]:
        """status, apply, status, doctor, uninstall for one harness; asserts each used d."""
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
        self.assertIn("No problems found.", out)
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



class UnsetTest(HarnessEnvCase):
    def test_each_harness_uses_its_default(self):
        for harness in HARNESSES:
            with self.subTest(harness=harness):
                d, _ = self.lifecycle(harness, None)
                self.assertTrue(str(d).startswith(str(self.home)))
                shutil.rmtree(d)  # uninstalled: the next harness's doctor run sees only itself


class EmptyTest(HarnessEnvCase):
    def test_each_harness_uses_its_default(self):
        for harness in HARNESSES:
            with self.subTest(harness=harness):
                d, _ = self.lifecycle(harness, "")
                self.assertEqual(d, self.home / HARNESSES[harness][1])
                shutil.rmtree(d)  # uninstalled: the next harness's doctor run sees only itself


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


if __name__ == "__main__":
    unittest.main()
