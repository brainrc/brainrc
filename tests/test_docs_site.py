"""The docs site (#197): mkdocs.yml's nav names real pages, and the build hook points links that
leave docs/ at GitHub."""
import importlib.util
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("mkdocs_hooks", REPO / "scripts" / "mkdocs_hooks.py")
hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hooks)


def page(src_uri: str):
    return SimpleNamespace(file=SimpleNamespace(src_uri=src_uri))


class DocsSiteTest(unittest.TestCase):
    def test_nav_names_pages_that_exist(self):
        nav = (REPO / "mkdocs.yml").read_text().split("\nnav:\n", 1)[1]
        pages = re.findall(r":\s*(\S+\.md)\s*$", nav, re.M)
        self.assertIn("index.md", pages)
        self.assertEqual([p for p in pages if not (REPO / "docs" / p).is_file()], [])

    def test_links_out_of_docs_go_to_github_and_others_stay(self):
        md = "[log](../CHANGELOG.md) [ex](../examples/pack-acme/README.md#top) [p](packs.md) [s](schemas/)"
        out = hooks.on_page_markdown(md, page("formats.md"))
        self.assertIn(f"]({hooks.BLOB}CHANGELOG.md)", out)
        self.assertIn(f"]({hooks.BLOB}examples/pack-acme/README.md#top)", out)
        self.assertIn("](packs.md)", out)
        self.assertIn("](schemas.md)", out)

    def test_a_relative_link_that_stays_in_docs_is_left_alone(self):
        self.assertEqual(hooks.on_page_markdown("[a](../install.md)", page("guides/x.md")), "[a](../install.md)")

    def test_every_schema_is_on_the_schemas_page(self):
        text = (REPO / "docs/schemas.md").read_text()
        for schema in (REPO / "docs/schemas").glob("*.json"):
            self.assertIn(f"(schemas/{schema.name})", text)

    def test_the_workflow_pins_its_tools(self):
        workflow = (REPO / ".github/workflows/docs.yml").read_text()
        for tool in ("mkdocs", "mkdocs-material", "mike"):
            self.assertRegex(workflow, rf"\b{tool}==\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
