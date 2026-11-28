"""The pack template (gh:151): examples/pack-template is `new pack` output, and it validates."""

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import REPO, TempRepoCase, brainrc, quiet  # noqa: E402

TEMPLATE = REPO / "examples" / "pack-template"


def load():
    spec = importlib.util.spec_from_file_location("pack_template", REPO / "scripts" / "pack_template.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SyncTest(unittest.TestCase):
    def test_template_matches_new_pack(self):
        self.assertEqual(load().differences(), [], "run scripts/pack_template.py --write")

    def test_a_change_shows(self):
        mod = load()
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d, "pack-template")
            shutil.copytree(TEMPLATE, copy)
            (copy / "rules/10-mypack.md").write_text("# changed\n", encoding="utf-8")
            (copy / "notes.md").write_text("mine\n", encoding="utf-8")
            (copy / "AGENTS.md").unlink()
            self.assertEqual(sorted(mod.differences(copy)),
                             ["differs rules/10-mypack.md", "extra notes.md", "missing AGENTS.md"])

    def test_pins_a_release_tag_everywhere(self):
        mod = load()
        version = mod.pinned()
        self.assertIsNotNone(version)
        tag = "v" + ".".join(map(str, version))
        self.assertIn(f"validate-pack@{tag}\n", (TEMPLATE / ".github/workflows/validate.yml").read_text())
        self.assertIn('requires_api = "^1"', (TEMPLATE / "pack.toml").read_text())

    def test_readme_says_how_to_make_it_yours(self):
        readme = (TEMPLATE / "README.md").read_text()
        self.assertTrue(readme.startswith("# mypack\n\nA template for a"))
        self.assertIn("brainrc new pack acme", readme)


class ValidTest(TempRepoCase):
    """It must pass on a first push: against the real core VERSION and the default pack (here the
    stand-in; CI also checks it with the validate-pack action against the real Gatework)."""

    def setUp(self):
        super().setUp()
        shutil.copy2(REPO / "VERSION", self.repo / "VERSION")
        shutil.copy2(REPO / "CHANGELOG.md", self.repo / "CHANGELOG.md")

    def test_template_is_valid_without_warnings(self):
        code, out = quiet(brainrc.cmd_validate, str(TEMPLATE))
        self.assertEqual(code, 0, out)
        self.assertNotIn("WARN", out)
        self.assertIn("(packs: gatework, mypack)", out)


if __name__ == "__main__":
    unittest.main()
