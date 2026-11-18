"""The docs site (#197): mkdocs.yml's nav names real pages, and the build hook points links that
leave docs/ at GitHub."""
import importlib.util
import os
import re
import unittest
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("mkdocs_hooks", REPO / "scripts" / "mkdocs_hooks.py")
hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hooks)


CONFIG = {"repo_url": "https://github.com/acme/brainrc/"}
BLOB = "https://github.com/acme/brainrc/blob/main/"


def page(src_uri: str):
    return SimpleNamespace(file=SimpleNamespace(src_uri=src_uri))


def render(md: str, src_uri: str = "formats.md") -> str:
    return hooks.on_page_markdown(md, page(src_uri), CONFIG)


class DocsSiteTest(unittest.TestCase):
    def test_nav_names_pages_that_exist(self):
        nav = (REPO / "mkdocs.yml").read_text(encoding="utf-8").split("\nnav:\n", 1)[1]
        pages = re.findall(r":\s*(\S+\.md)\s*$", nav, re.M)
        self.assertIn("index.md", pages)
        self.assertEqual([p for p in pages if not (REPO / "docs" / p).is_file()], [])

    def test_links_out_of_docs_go_to_github_and_others_stay(self):
        md = '[log](../CHANGELOG.md) [ex](../examples/pack-acme/README.md#top) [t](../VERSION "v") [p](packs.md)'
        out = render(md)
        self.assertIn(f"]({BLOB}CHANGELOG.md)", out)
        self.assertIn(f"]({BLOB}examples/pack-acme/README.md#top)", out)
        self.assertIn(f'](https://github.com/acme/brainrc/blob/main/VERSION "v")', out)
        self.assertIn("](packs.md)", out)

    def test_a_relative_link_that_stays_in_docs_is_left_alone(self):
        self.assertEqual(render("[a](../install.md)", "guides/x.md"), "[a](../install.md)")

    def test_links_inside_code_are_left_alone(self):
        md = (
            "`[a](../a.md)` ``[b](../b.md) ` x`` \n\n"
            "- item\n\n  ```md\n  [c](../c.md)\n  ```\n\n"
            "````md\n```\n[d](../d.md)\n```\n[e](../e.md)\n````\n\n[f](../f.md)"
        )
        out = render(md)
        for kept in ("[a](../a.md)", "[b](../b.md)", "[c](../c.md)", "[d](../d.md)", "[e](../e.md)"):
            self.assertIn(kept, out)
        self.assertIn(f"]({BLOB}f.md)", out)

    def test_without_a_repo_url_links_stay_as_written(self):
        md = "[log](../CHANGELOG.md)"
        self.assertEqual(hooks.on_page_markdown(md, page("formats.md"), {"repo_url": None}), md)

    def test_a_published_version_links_to_its_own_tag(self):
        with unittest.mock.patch.dict(os.environ, {"BRAINRC_DOCS_REF": "v1.2.3"}):
            out = render("[log](../CHANGELOG.md)")
        self.assertIn("](https://github.com/acme/brainrc/blob/v1.2.3/CHANGELOG.md)", out)

    def test_docs_link_to_pages_not_directories(self):
        directory = re.compile(r"\]\((?![a-z]+:)[^)#\s]*/(?:#[^)\s]*)?(?:\s+\"[^\"]*\")?\)")
        docs = REPO / "docs"
        bad = {str(p.relative_to(docs)) for p in docs.rglob("*.md") if directory.search(p.read_text(encoding="utf-8"))}
        self.assertEqual(bad, set())

    def test_every_schema_is_on_the_schemas_page(self):
        text = (REPO / "docs/schemas.md").read_text(encoding="utf-8")
        for schema in (REPO / "docs/schemas").glob("*.json"):
            self.assertIn(f"(schemas/{schema.name})", text)

    def test_the_tools_are_pinned_with_hashes(self):
        reqs = (REPO / ".github/docs-requirements.txt").read_text(encoding="utf-8")
        for tool in ("mkdocs", "mkdocs-material", "mike"):
            self.assertRegex(reqs, rf"(?m)^{tool}==\d+\.\d+\.\d+ ")
        pins = re.findall(r"(?m)^[a-z0-9_.-]+==\S+(?:\s*\\\n\s*--hash=sha256:[0-9a-f]{64})+", reqs)
        self.assertEqual(len(pins), len(re.findall(r"(?m)^[a-z0-9_.-]+==", reqs)))
        workflow = (REPO / ".github/workflows/docs.yml").read_text(encoding="utf-8")
        self.assertNotRegex(workflow, r"pip install (?!--require-hashes)")

if __name__ == "__main__":
    unittest.main()
