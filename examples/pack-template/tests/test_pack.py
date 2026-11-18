"""mypack's own tests: `brainrc validate --pack .` runs them (`test` in pack.toml).

A guard hook is tested with brainrc.testing (assert_asks, assert_allows, ...), which validate puts
on the path: see "Pack tests" in brainrc's docs/packs.md.
"""
import os
import re
import unittest
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent
TEXT = {".md", ".toml", ".json", ".yaml", ".yml", ".py", ".txt"}
SECRET = re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*[\"']?[\w/+.=-]{12,}")


SKIP = {"node_modules", "venv", "__pycache__"}  # and dot-folders but .github: .git, .venv, caches


def text_files():
    for root, dirs, names in os.walk(PACK):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and (d == ".github" or not d.startswith(".")))
        for name in sorted(names):
            if Path(name).suffix in TEXT:
                yield Path(root, name)


class RulesTest(unittest.TestCase):
    def test_rules_stay_short(self):
        # Rules load in every session on every machine with this pack: detail goes in a skill.
        for rule in sorted((PACK / "rules").glob("*.md")):
            lines = [line for line in rule.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertLessEqual(len(lines), 30, f"{rule.name}: move the detail into a skill")


class SecretsTest(unittest.TestCase):
    def test_no_secret_values(self):
        for path in text_files():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if SECRET.search(line):  # named, never printed
                    self.fail(f"{path.relative_to(PACK).as_posix()}:{n} looks like a secret")


if __name__ == "__main__":
    unittest.main()
