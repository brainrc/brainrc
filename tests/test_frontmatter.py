"""Frontmatter parsing (#171): block scalars, quotes, comments and continued plain scalars."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brainrc.sources import frontmatter  # noqa: E402


def parse(text: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "SKILL.md"
        path.write_text(text)
        return frontmatter(path)


class FrontmatterTest(unittest.TestCase):
    def test_plain_values_and_comments(self):
        meta = parse("---\nname: x\ndescription: Does a thing  # why\nmodel: sonnet\n---\nbody\n")
        self.assertEqual(meta, {"name": "x", "description": "Does a thing", "model": "sonnet"})

    def test_folded_scalar(self):
        meta = parse("---\nname: x\ndescription: >\n  Drive a ticket\n  to a reviewed PR.\n\n  Use it often.\n"
                     "tools: Read\n---\n")
        self.assertEqual(meta["description"], "Drive a ticket to a reviewed PR.\nUse it often.\n")
        self.assertEqual(meta["tools"], "Read")

    def test_folded_strip_and_keep(self):
        self.assertEqual(parse("---\nd: >-\n  a\n  b\n---\n")["d"], "a b")
        self.assertEqual(parse("---\nd: >+\n  a\n\n---\n")["d"], "a\n\n")

    def test_literal_scalar(self):
        meta = parse("---\ndescription: |\n  line one\n    indented\n  line two\nname: y\n---\n")
        self.assertEqual(meta["description"], "line one\n  indented\nline two\n")
        self.assertEqual(meta["name"], "y")

    def test_literal_strip_and_indent_indicator(self):
        self.assertEqual(parse("---\nd: |-\n  a\n  b\n---\n")["d"], "a\nb")
        self.assertEqual(parse("---\nd: |2\n    a\n  b\n---\n")["d"], "  a\nb\n")

    def test_folded_more_indented_lines_keep_newlines(self):
        self.assertEqual(parse("---\nd: >\n  a\n    code\n  b\n---\n")["d"], "a\n  code\nb\n")

    def test_block_scalar_with_a_comment_after_the_indicator(self):
        self.assertEqual(parse("---\nd: >  # folded\n  a\n  b\n---\n")["d"], "a b\n")

    def test_empty_block_scalar(self):
        self.assertEqual(parse("---\nd: |\nname: x\n---\n"), {"d": "", "name": "x"})

    def test_quoted_values(self):
        meta = parse("---\na: \"x # not a comment\"  # comment\nb: 'it''s'\nc: \"tab\\there\"\n---\n")
        self.assertEqual(meta, {"a": "x # not a comment", "b": "it's", "c": "tab\there"})

    def test_plain_scalar_continued_on_indented_lines(self):
        meta = parse("---\ndescription: Drive a ticket\n  to a reviewed PR.\nname: x\n---\n")
        self.assertEqual(meta["description"], "Drive a ticket to a reviewed PR.")

    def test_flow_values_stay_as_written(self):
        self.assertEqual(parse("---\nargument-hint: [ticket ref or slug]\n---\n")["argument-hint"],
                         "[ticket ref or slug]")

    def test_no_or_unterminated_frontmatter(self):
        self.assertEqual(parse("# Title\n"), {})
        self.assertEqual(parse("---\nname: x\n"), {})

    def test_a_long_folded_description_passes_validate_checks(self):
        meta = parse("---\nname: x\ndescription: >\n  " + "word " * 10 + "\n---\n")
        self.assertTrue(meta["description"].startswith("word word"))


if __name__ == "__main__":
    unittest.main()
