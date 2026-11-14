"""The brainrc.toml and brainrc.lock contract (#281): the JSON Schemas in docs/schemas/ accept
every valid fixture and reject every invalid one with the error each fixture names."""
import json
import re
import sys
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brainrc import schema  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests/fixtures/lockfile"
SCHEMAS = {".toml": "brainrc.toml", ".lock": "brainrc.lock"}


def check(path: Path) -> list[str]:
    return schema.errors(tomllib.loads(path.read_text(encoding="utf-8")), schema.load(SCHEMAS[path.suffix]))


class ConformanceTest(unittest.TestCase):
    def test_fixtures_exist_for_both_files(self):
        for kind in ("valid", "invalid"):
            suffixes = {p.suffix for p in (FIXTURES / kind).iterdir()}
            self.assertEqual(suffixes, {".toml", ".lock"}, kind)

    def test_valid_fixtures_conform(self):
        for path in sorted((FIXTURES / "valid").iterdir()):
            with self.subTest(path.name):
                self.assertEqual(check(path), [])

    def test_invalid_fixtures_fail_with_their_error(self):
        for path in sorted((FIXTURES / "invalid").iterdir()):
            with self.subTest(path.name):
                expect = re.match(r"# expect: (.+)\n", path.read_text(encoding="utf-8"))
                self.assertIsNotNone(expect, "an invalid fixture starts with `# expect: <error>`")
                found = check(path)
                self.assertTrue(found, "accepted")
                self.assertTrue(any(expect[1] in e for e in found), found)


class SchemaFilesTest(unittest.TestCase):
    def test_schemas_are_draft_2020_12_and_documented(self):
        doc = (REPO / "docs/project.md").read_text(encoding="utf-8")
        for name in SCHEMAS.values():
            data = json.loads((REPO / f"docs/schemas/{name}.schema.json").read_text(encoding="utf-8"))
            self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertIn(f"schemas/{name}.schema.json", doc)

    def test_the_validator_knows_every_keyword_the_schemas_use(self):
        known = {"$schema", "$id", "title", "description", "$defs", "type", "const", "enum",
                 "pattern", "minLength", "items", "properties", "required",
                 "additionalProperties", "propertyNames", "$ref", "not", "oneOf", "anyOf"}

        def keywords(node, under_props=False):
            if isinstance(node, dict):
                for key, value in node.items():
                    if not under_props:
                        yield key
                    yield from keywords(value, key in ("properties", "$defs"))
            elif isinstance(node, list):
                for item in node:
                    yield from keywords(item)

        for name in SCHEMAS.values():
            used = set(keywords(schema.load(name)))
            self.assertEqual(used - known, set(), name)

    def test_doc_examples_conform(self):
        doc = (REPO / "docs/project.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```toml\n(.*?)```", doc, re.S)
        self.assertEqual(len(blocks), 2)
        manifest = tomllib.loads(blocks[0])
        self.assertEqual(schema.errors(manifest, schema.load("brainrc.toml")), [])
        lock = tomllib.loads(re.sub(r'"sha256:[0-9a-f]+…"', '"sha256:' + "0" * 64 + '"', blocks[1]))
        self.assertEqual(schema.errors(lock, schema.load("brainrc.lock")), [])


class ValidatorTest(unittest.TestCase):
    def test_errors_name_where_and_what(self):
        s = {"type": "object", "additionalProperties": False, "required": ["a"],
             "properties": {"a": {"type": "integer"}, "b": {"enum": ["x"]}}}
        self.assertEqual(schema.errors({"a": True, "b": "y", "c": 1}, s),
                         ["a: must be an integer", "b: must be one of \"x\"", "the file: unknown key `c`"])

    def test_bool_is_not_an_integer_and_ref_resolves(self):
        s = {"$defs": {"n": {"type": "integer"}}, "type": "array", "items": {"$ref": "#/$defs/n"}}
        self.assertEqual(schema.errors([1, 2], s), [])
        self.assertEqual(schema.errors([1, False], s), ["[1]: must be an integer"])


if __name__ == "__main__":
    unittest.main()
