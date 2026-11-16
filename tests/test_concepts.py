"""The README opens with one sentence on what brainrc is, and docs/concepts.md defines its words (#296)."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class ConceptsTest(unittest.TestCase):
    def test_readme_opens_with_one_sentence(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        first = text.split("\n\n")[1].strip()  # the paragraph after the `# brainrc` title
        self.assertTrue(first.startswith("brainrc "), first)
        self.assertEqual(len(re.findall(r"[.!?](\s|$)", first)), 1, f"one sentence: {first}")
        self.assertIn("(docs/concepts.md)", text.split("\n## ", 1)[0], "the lead links the concepts page")

    def test_concepts_defines_the_four_words(self):
        headings = re.findall(r"^## (.+)$", (REPO / "docs/concepts.md").read_text(encoding="utf-8"), re.M)
        for word in ("Pack", "Harness", "Profile", "Lockfile"):
            self.assertIn(word, headings)


if __name__ == "__main__":
    unittest.main()
