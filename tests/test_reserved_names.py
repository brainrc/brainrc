"""validate rejects core skills that take a reserved built-in name (149.2, AC1-AC3)."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, make_pack, quiet, set_core_version  # noqa: E402
from support import rmtree


class ReservedNamesTest(TempRepoCase):
    def add_core_skill(self, name):
        d = self.repo / "packs/gatework/skills" / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: A test skill.\n---\nBody.\n")

    def test_shipped_tree_passes(self):
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_reserved_core_skill_fails_naming_it(self):
        for name in ("review", "plan", "init", "help", "status", "compact"):
            with self.subTest(name=name):
                self.add_core_skill(name)
                try:
                    code, out = quiet(brainrc.cmd_validate)
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"skills/{name}", out)
                    self.assertIn("reserved", out)
                finally:
                    (self.repo / "packs/gatework/skills" / name / "SKILL.md").unlink()
                    (self.repo / "packs/gatework/skills" / name).rmdir()

class ReservedNamesPackTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")

    def tearDown(self):
        rmtree(self.pack.parent)
        super().tearDown()

    def add_pack_skill(self, name):
        (self.pack / "skills" / name).mkdir()
        (self.pack / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n")

    def test_pack_skill_is_not_checked_for_reserved_names(self):
        self.add_pack_skill("status")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertNotIn("reserved", out)

    def test_core_and_pack_duplicate_still_reported(self):
        self.add_pack_skill("spec-agent")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1, out)
        self.assertIn("skill `spec-agent` is defined in both gatework and acme", out)


if __name__ == "__main__":
    unittest.main()
