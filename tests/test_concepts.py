"""The README opens with one sentence on what brainrc is, and docs/concepts.md defines its words (#296)."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def lead(readme: str) -> str:
    """The first prose paragraph after the `# brainrc` title, skipping badges and comments."""
    body = readme.split("\n", 1)[1]
    for para in body.split("\n\n"):
        para = para.strip()
        if para and not para.startswith(("<!--", "[![", "![")):
            return para
    return ""


class ConceptsTest(unittest.TestCase):
    def test_readme_opens_with_one_sentence(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        first = lead(text)
        self.assertTrue(first.startswith("brainrc "), first)
        plain = re.sub(r"[*`_]", "", first)  # sentence ends hide behind markup: `.**`
        ends = re.findall(r"[.!?](?=\s+[A-Z]|\s*$)", plain)
        self.assertEqual(len(ends), 1, f"one sentence: {first}")
        self.assertIn("(docs/concepts.md)", text.split("\n## ", 1)[0], "the lead links the concepts page")

    def test_concepts_defines_its_words(self):
        headings = re.findall(r"^## (.+)$", (REPO / "docs/concepts.md").read_text(encoding="utf-8"), re.M)
        for word in ("Harness", "Item", "Pack", "Profile", "Lockfile", "Scope"):
            self.assertIn(word, headings)


if __name__ == "__main__":
    unittest.main()
