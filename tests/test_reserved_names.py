"""validate rejects core skills that take a reserved built-in name (149.2, AC1-AC3)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet  # noqa: E402


class ReservedNamesTest(TempRepoCase):
    def add_core_skill(self, name):
        d = self.repo / "skills" / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: A test skill.\n---\nBody.\n")

    def test_shipped_tree_passes(self):
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_reserved_core_skill_fails_naming_it(self):
        for name in ("init", "help", "status", "compact"):
            with self.subTest(name=name):
                self.add_core_skill(name)
                try:
                    code, out = quiet(brainrc.cmd_validate)
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"skills/{name}", out)
                    self.assertIn("reserved", out)
                finally:
                    (self.repo / "skills" / name / "SKILL.md").unlink()
                    (self.repo / "skills" / name).rmdir()

    def test_declared_aliases_are_exempt(self):
        for name in ("review", "plan"):
            with self.subTest(name=name):
                self.assertIn(name, brainrc.validate.DEPRECATED_ALIASES)
                self.assertIn(name, brainrc.validate.RESERVED_SKILL_NAMES)


if __name__ == "__main__":
    unittest.main()
