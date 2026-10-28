"""Contract tests for the brainrc entry points and the deprecated aicfg shims (spec 205)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEPRECATED_ENTRY = (
    "import sys; from brainrc.cli import deprecated_entry; "
    "sys.argv=['aicfg']+sys.argv[1:]; deprecated_entry()"
)


class EntryPointCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env = {k: v for k, v in os.environ.items() if k != "PYTHONWARNINGS"}
        self.env.update(HOME=tmp.name, AICFG_HOME=str(Path(tmp.name) / "ai-config"))

    def run_py(self, *args):
        return subprocess.run(
            [sys.executable, *args], cwd=REPO, env=self.env, capture_output=True, text=True, timeout=120,
        )

    def assert_warns_deprecated(self, proc):
        self.assertIn("brainrc", proc.stderr)
        self.assertIn("0.5.0", proc.stderr)

    def assert_same_result(self, old, new):
        self.assertEqual(old.stdout, new.stdout)
        self.assertEqual(old.returncode, new.returncode)

    def assert_warned_once_off_stdout(self, proc):
        self.assertEqual(proc.stderr.count("0.5.0"), 1, proc.stderr)
        self.assertNotIn("0.5.0", proc.stdout)
        self.assertNotIn("deprecated", proc.stdout.lower())


class TestDeprecatedConsoleScript(EntryPointCase):
    def test_ac3_aicfg_status_warns_and_matches_brainrc(self):
        old = self.run_py("-c", DEPRECATED_ENTRY, "status")
        new = self.run_py("-m", "brainrc", "status")
        self.assert_warns_deprecated(old)
        self.assert_same_result(old, new)

    def test_ac3_aicfg_version_matches_brainrc(self):
        old = self.run_py("-c", DEPRECATED_ENTRY, "--version")
        new = self.run_py("-m", "brainrc", "--version")
        self.assert_warns_deprecated(old)
        self.assertEqual(new.returncode, 0)
        self.assert_same_result(old, new)

    def test_ac11_console_script_warns_once_never_on_stdout(self):
        self.assert_warned_once_off_stdout(self.run_py("-c", DEPRECATED_ENTRY, "status"))


class TestScripts(EntryPointCase):
    def test_ac4_scripts_brainrc_validate_has_no_warning(self):
        proc = self.run_py("scripts/brainrc.py", "validate")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("deprecat", proc.stderr.lower())
        self.assertNotIn("0.5.0", proc.stderr)

    def test_ac5_scripts_aicfg_validate_warns_and_matches_brainrc(self):
        old = self.run_py("scripts/aicfg.py", "validate", "--pack", ".")
        new = self.run_py("scripts/brainrc.py", "validate", "--pack", ".")
        self.assert_warns_deprecated(old)
        self.assert_same_result(old, new)

    def test_ac11_scripts_aicfg_warns_once_never_on_stdout(self):
        self.assert_warned_once_off_stdout(self.run_py("scripts/aicfg.py", "validate", "--pack", "."))


class TestModuleEntry(EntryPointCase):
    def test_ac6_python_m_brainrc_works_without_warning(self):
        proc = self.run_py("-m", "brainrc", "status")
        self.assertNotIn("deprecat", proc.stderr.lower())
        self.assertNotIn("0.5.0", proc.stderr)
        self.assertIn(proc.returncode, (0, 1), proc.stderr)

    def test_ac6_python_m_aicfg_warns_and_matches_brainrc(self):
        old = self.run_py("-m", "aicfg", "status")
        new = self.run_py("-m", "brainrc", "status")
        self.assert_warns_deprecated(old)
        self.assert_same_result(old, new)

    def test_ac11_python_m_aicfg_warns_once_never_on_stdout(self):
        self.assert_warned_once_off_stdout(self.run_py("-m", "aicfg", "--version"))


class TestAicfgImport(EntryPointCase):
    def test_ac7_import_aicfg_emits_deprecation_warning(self):
        proc = self.run_py("-W", "error::DeprecationWarning", "-c", "import aicfg")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("DeprecationWarning", proc.stderr)
        self.assertIn("brainrc", proc.stderr)

    def test_ac7_aicfg_cli_main_is_brainrc_cli_main(self):
        code = "import aicfg.cli, brainrc.cli; assert aicfg.cli.main is brainrc.cli.main"
        proc = self.run_py("-W", "ignore::DeprecationWarning", "-c", code)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
