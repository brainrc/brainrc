"""Contract tests for the brainrc entry points and that the aicfg names are gone (specs 205, 238)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import home_env

REPO = Path(__file__).resolve().parent.parent


class EntryPointCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env = {k: v for k, v in os.environ.items() if k != "PYTHONWARNINGS"}
        home = Path(tmp.name).resolve()
        self.env.update(home_env(home), BRAINRC_HOME=str(home / "brainrc"))

    def run_py(self, *args):
        return subprocess.run(
            [sys.executable, *args], cwd=REPO, env=self.env, capture_output=True, text=True, timeout=120,
        )

    def assert_no_deprecation(self, proc):
        self.assertNotIn("deprecat", proc.stderr.lower())
        self.assertNotIn("0.5.0", proc.stderr)

class TestScripts(EntryPointCase):
    def test_scripts_brainrc_validate_has_no_warning(self):
        proc = self.run_py("scripts/brainrc.py", "validate")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assert_no_deprecation(proc)

    def test_scripts_aicfg_is_gone(self):
        self.assertFalse((REPO / "scripts/aicfg.py").exists())
        self.assertFalse((REPO / "aicfg").exists())

class TestModuleEntry(EntryPointCase):
    def test_python_m_brainrc_works_without_warning(self):
        proc = self.run_py("-m", "brainrc", "status")
        self.assert_no_deprecation(proc)
        self.assertIn(proc.returncode, (0, 1), proc.stderr)

    def test_python_m_aicfg_and_import_aicfg_are_gone(self):
        self.assertNotEqual(self.run_py("-m", "aicfg", "--version").returncode, 0)
        self.assertNotEqual(self.run_py("-c", "import aicfg").returncode, 0)

    def test_no_command_prints_a_deprecation_line_for_the_old_home_vars(self):
        self.env["AICFG_HOME"] = str(Path(self.env["HOME"]) / "old")
        del self.env["BRAINRC_HOME"]
        proc = self.run_py("-m", "brainrc", "--version")
        self.assertEqual(proc.stderr, "")

if __name__ == "__main__":
    unittest.main()
