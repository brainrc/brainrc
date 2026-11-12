"""Namespaced skills (specs/149-1-namespaced-skills). Gatework's own skills, and the tests of their
names, live in brainrc/gatework; what stays here is core's side."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet, set_core_version  # noqa: E402


class RemovedAliasesTest(unittest.TestCase):
    """The old names were removed in 0.6.1, as announced for 0.6.0."""

    def test_alias_check_is_gone(self):
        self.assertFalse(hasattr(brainrc.validate, "DEPRECATED_ALIASES"))
        self.assertFalse(hasattr(brainrc.validate, "_check_aliases"))


class PluginManifestTest(TempRepoCase):
    """validate catches a stale plugin manifest."""

    def test_stale_manifest_fails_validate(self):
        quiet(brainrc.cmd_plugin)
        self.assertEqual(brainrc.check_plugin(), [])
        set_core_version(self.repo, "9.9.9")  # the manifests carry VERSION
        errors = brainrc.check_plugin()
        self.assertTrue(any("stale" in e for e in errors), errors)
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("brainrc.py plugin", out)


if __name__ == "__main__":
    unittest.main()
