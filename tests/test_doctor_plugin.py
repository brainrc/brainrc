"""Doctor's old `ai-config` plugin findings (spec 208, AC7 to AC11), against a temp HOME."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from brainrc.doctor import _plugin_findings, cmd_doctor

HOME_VARS = ("HOME", "BRAINRC_HOME", "AICFG_HOME", "XDG_CONFIG_HOME")


class TestPluginFindings(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name).resolve() / "home"
        self.home.mkdir()
        self.installed = self.home / ".claude" / "plugins" / "installed_plugins.json"
        self.cursor = self.home / ".cursor" / "plugins" / "local"

    def findings(self):
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env["HOME"] = str(self.home)
        with mock.patch.dict(os.environ, env, clear=True):
            return _plugin_findings()

    def write_installed(self, data):
        self.installed.parent.mkdir(parents=True, exist_ok=True)
        self.installed.write_text(data if isinstance(data, str) else json.dumps(data))

    def assert_claude_warn(self, found):
        [(level, what, fix)] = found
        self.assertEqual(level, "WARN")
        self.assertIn("installed_plugins.json", what)
        self.assertIn("ai-config@ai-config", what)
        self.assertIn("/plugin uninstall ai-config@ai-config", fix)
        self.assertIn("/plugin marketplace remove ai-config", fix)

    def test_claude_old_plugin_warns(self):
        self.write_installed({"plugins": {"ai-config@ai-config": [{}]}})
        self.assert_claude_warn(self.findings())

    def test_claude_old_next_to_new_still_warns(self):
        self.write_installed({"plugins": {"ai-config@ai-config": [], "brainrc@brainrc": []}})
        self.assert_claude_warn(self.findings())

    def test_claude_no_finding_cases(self):
        cases = [
            {"plugins": {"brainrc@brainrc": []}},
            {"plugins": {"ai-config@other": [], "other@ai-config": [], "x@y": []}},
            {"plugins": {}},
            {"version": 2},
            {"plugins": ["ai-config@ai-config"]},
            ["ai-config@ai-config"],
            "not json {",
            "",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.write_installed(case)
                self.assertEqual(self.findings(), [])

    def test_claude_missing_file_no_finding(self):
        self.assertEqual(self.findings(), [])

    def test_claude_unreadable_file_no_finding(self):
        self.installed.mkdir(parents=True)  # a directory: reading it raises OSError
        self.assertEqual(self.findings(), [])

    def test_claude_undecodable_file_no_finding(self):
        self.installed.parent.mkdir(parents=True)
        self.installed.write_bytes(b"\xff\xfe\x00")
        self.assertEqual(self.findings(), [])

    def test_claude_deeply_nested_file_no_finding(self):
        self.write_installed("[" * 200000)
        self.assertEqual(self.findings(), [])

    def test_claude_file_over_1mb_is_skipped(self):
        pad = "x" * (1024 * 1024)
        self.write_installed({"pad": pad, "plugins": {"ai-config@ai-config": []}})
        self.assertEqual(self.findings(), [])

    def test_claude_file_is_read_as_utf8(self):
        self.write_installed({"plugins": {"ai-config@ai-config": [], "caf\u00e9@x": []}})
        real = Path.read_text
        seen = []

        def spy(path, *a, **kw):
            seen.append(kw.get("encoding"))
            return real(path, *a, **kw)

        with mock.patch.object(Path, "read_text", spy):
            self.assert_claude_warn(self.findings())
        self.assertEqual(seen, ["utf-8"])

    def test_cursor_unsearchable_parent_no_finding_and_no_error(self):
        if os.geteuid() == 0:
            self.skipTest("chmod 000 does not restrict root")
        (self.cursor / "ai-config").mkdir(parents=True)
        self.cursor.chmod(0)
        self.addCleanup(self.cursor.chmod, 0o755)
        self.assertEqual(self.findings(), [])

    def test_cursor_oserror_on_check_no_finding(self):
        (self.cursor / "ai-config").mkdir(parents=True)
        with mock.patch.object(Path, "is_symlink", side_effect=PermissionError):
            self.assertEqual(self.findings(), [])

    def assert_cursor_warn(self, found):
        [(level, what, fix)] = found
        self.assertEqual(level, "WARN")
        self.assertIn("~/.cursor/plugins/local/ai-config", what)
        self.assertIn("old", what)
        self.assertIn("remove the link (or directory) at ~/.cursor/plugins/local/ai-config", fix)
        self.assertNotIn("rm ", fix)
        self.assertIn("brainrc", fix)

    def test_cursor_old_directory_warns(self):
        (self.cursor / "ai-config").mkdir(parents=True)
        self.assert_cursor_warn(self.findings())

    def test_cursor_old_symlink_warns_even_when_broken(self):
        self.cursor.mkdir(parents=True)
        (self.cursor / "ai-config").symlink_to(self.home / "gone")
        self.assert_cursor_warn(self.findings())

    def test_cursor_old_next_to_new_still_warns(self):
        (self.cursor / "ai-config").mkdir(parents=True)
        (self.cursor / "brainrc").mkdir()
        self.assert_cursor_warn(self.findings())

    def test_cursor_only_new_or_absent_no_finding(self):
        self.assertEqual(self.findings(), [])
        (self.cursor / "brainrc").mkdir(parents=True)
        self.assertEqual(self.findings(), [])

    def test_both_harnesses_give_two_warnings_and_write_nothing(self):
        self.write_installed({"plugins": {"ai-config@ai-config": []}})
        (self.cursor / "ai-config").mkdir(parents=True)
        before = sorted(p for p in self.home.rglob("*"))
        content = self.installed.read_text()
        self.assertEqual(len(self.findings()), 2)
        self.assertEqual(sorted(self.home.rglob("*")), before)
        self.assertEqual(self.installed.read_text(), content)

    def test_warnings_do_not_change_exit_code(self):
        self.write_installed({"plugins": {"ai-config@ai-config": []}})
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env["HOME"] = str(self.home)
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch("brainrc.doctor.doctor_findings", return_value=_plugin_findings()), \
                mock.patch("builtins.print"):
            self.assertEqual(cmd_doctor(), 0)


if __name__ == "__main__":
    unittest.main()
