"""docs/capabilities.md is generated from harnesses.toml (#298); this fails when they disagree."""
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from brainrc import capabilities  # noqa: E402


class CapabilitiesTest(unittest.TestCase):
    def test_page_matches_harnesses_toml(self):
        page = capabilities.current((REPO / capabilities.PAGE).read_text())
        self.assertIsNotNone(page, "docs/capabilities.md lost its BEGIN/END marker lines")
        self.assertEqual(page, capabilities.render(REPO),
                         "docs/capabilities.md is stale: run `python3 scripts/brainrc.py capabilities --write`")

    def test_one_row_per_harness_with_its_label(self):
        harnesses = tomllib.loads((REPO / "harnesses.toml").read_text())
        rows = capabilities.render(REPO).splitlines()[2:]
        self.assertEqual(len(rows), len(harnesses))
        self.assertEqual(set(harnesses) - set(capabilities.LABELS), set(), "name the new tool in LABELS")

    def test_a_changed_harness_makes_the_page_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            shutil.copy(REPO / capabilities.PAGE, root / capabilities.PAGE)
            shutil.copytree(REPO / "overrides", root / "overrides")
            toml = (REPO / "harnesses.toml").read_text()
            changed = toml.replace("\n[codex]\n", "\n[codex]\nagents = \"~/.codex/agents\"\n", 1)
            self.assertNotEqual(changed, toml, "the [codex] table moved: update this test")
            (root / "harnesses.toml").write_text(changed)
            self.assertNotEqual(capabilities.current((root / capabilities.PAGE).read_text()), capabilities.render(root))
            self.assertTrue(capabilities.write(root))
            self.assertEqual(capabilities.current((root / capabilities.PAGE).read_text()), capabilities.render(root))
            self.assertFalse(capabilities.write(root))

    def test_write_refuses_a_page_without_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / capabilities.PAGE).write_text("# no table\n")
            shutil.copy(REPO / "harnesses.toml", root / "harnesses.toml")
            with self.assertRaises(capabilities.ConfigError):
                capabilities.write(root)


if __name__ == "__main__":
    unittest.main()
