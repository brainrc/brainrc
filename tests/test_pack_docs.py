"""Pack author docs (gh:152): one Divio type per page, all in the nav, key tables from the schemas."""

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MARKER = re.compile(r"<!-- divio: ([a-z-]+) -->")
TYPES = {"tutorial", "how-to", "reference", "explanation"}


def pack_pages() -> list[Path]:
    return [DOCS / "tutorial.md", DOCS / "packs.md", *sorted((DOCS / "packs").glob("*.md"))]


def load_reference():
    spec = importlib.util.spec_from_file_location("pack_reference", ROOT / "scripts" / "pack_reference.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class DivioTest(unittest.TestCase):
    def test_each_page_has_one_type_on_its_first_line(self):
        for page in pack_pages():
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                found = MARKER.findall(text)
                self.assertEqual(len(found), 1, "one divio marker")
                self.assertIn(found[0], TYPES)
                self.assertTrue(text.startswith(f"<!-- divio: {found[0]} -->\n# "), "marker, then the title")

    def test_every_type_is_covered(self):
        found = {MARKER.search(p.read_text(encoding="utf-8"))[1] for p in pack_pages()}
        self.assertEqual(found, TYPES)

    def test_the_asked_for_how_tos_exist(self):
        for name in ("employer-pack", "team-pack", "personal-pack", "stack-pack", "from-a-plugin"):
            with self.subTest(name=name):
                text = (DOCS / "packs" / f"{name}.md").read_text(encoding="utf-8")
                self.assertTrue(text.startswith("<!-- divio: how-to -->"))

    def test_every_page_is_in_the_nav(self):
        nav = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        for page in pack_pages():
            with self.subTest(page=page.name):
                self.assertIn(f": {page.relative_to(DOCS).as_posix()}\n", nav)

    def test_gatework_not_spec_agent(self):
        # spec-agent is named only where a paragraph is about its old names
        for page in pack_pages():
            for para in page.read_text(encoding="utf-8").split("\n\n"):
                if "spec-agent" in para:
                    with self.subTest(page=page.name, para=para[:60]):
                        self.assertIn("old", para)


class ReferenceTest(unittest.TestCase):
    def test_committed_tables_match_the_schemas(self):
        mod = load_reference()
        doc = mod.DOC.read_text(encoding="utf-8")
        self.assertEqual(mod.render(doc), doc, "run scripts/pack_reference.py --write")

    def test_a_changed_schema_shows(self):
        mod = load_reference()
        doc = mod.DOC.read_text(encoding="utf-8")
        stale = doc.replace("| `test` | string |", "| `test` | number |")
        self.assertNotEqual(stale, doc)
        self.assertEqual(mod.render(stale), doc)

    def test_links_and_brackets(self):
        mod = load_reference()
        schema = {"properties": {"a": {"type": "string", "description": "An <id> (docs/packs.md#naming), or (docs/formats.md#rules)."}}}
        row = mod.table(schema, ("properties",)).splitlines()[-1]
        self.assertEqual(row, "| `a` | string | An &lt;id> ([naming](#naming)), or ([rules](formats.md#rules)). |")


if __name__ == "__main__":
    unittest.main()
