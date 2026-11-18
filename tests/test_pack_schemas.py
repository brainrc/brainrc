"""Published JSON Schemas for pack.toml, mcp/servers.toml and harnesses.toml (#135): editors complete
from them (.taplo.toml, the `#:schema` line), and validate checks a pack's pack.toml against its own,
warning on a key it doesn't know."""
import json
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet  # noqa: E402
from brainrc import config, mcp, opencode, schema  # noqa: E402
from brainrc.scaffold import PACK_SCHEMA, PackSpec, Rule, Skill, render_pack, write_pack  # noqa: E402
from support import rmtree  # noqa: E402

NEW = ("pack.toml", "mcp-servers.toml", "harnesses.toml")


def load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


class SchemaFilesTest(unittest.TestCase):
    def test_draft_2020_12_with_an_id_that_matches_the_file(self):
        for name in NEW:
            with self.subTest(name=name):
                data = json.loads((ROOT / f"docs/schemas/{name}.schema.json").read_text(encoding="utf-8"))
                self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertTrue(data["$id"].endswith(f"/docs/schemas/{name}.schema.json"))

    def test_shipped_files_conform(self):
        cases = [("pack.toml", ROOT / "examples/pack-acme/pack.toml"),
                 ("pack.toml", ROOT / "examples/pack-homelab/pack.toml"),
                 ("pack.toml", ROOT / "tests/fixtures/default-pack/pack.toml"),
                 ("mcp-servers.toml", ROOT / "mcp/servers.toml"),
                 ("harnesses.toml", ROOT / "harnesses.toml")]
        for name, path in cases:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertEqual(schema.errors(load_toml(path), schema.load(name)), [])

    def test_the_commented_server_examples_conform(self):
        text = (ROOT / "mcp/servers.toml").read_text(encoding="utf-8")
        uncommented = "\n".join(line[2:] for line in text.splitlines()
                                if line.startswith("# ") and ("=" in line or line.startswith("# [")))
        data = tomllib.loads(uncommented)
        self.assertGreaterEqual(len(data["servers"]), 2)
        self.assertEqual(schema.errors(data, schema.load("mcp-servers.toml")), [])

    def test_schemas_list_the_keys_the_code_reads(self):
        server = schema.load("mcp-servers.toml")["$defs"]["server"]
        self.assertEqual(set(server["properties"]), mcp.SERVER_KEYS)
        harness = schema.load("harnesses.toml")["$defs"]["harness"]
        self.assertEqual(set(harness["properties"]), set(config.LAYERED_KEYS["harnesses"]))
        self.assertEqual(harness["properties"]["agents_format"]["enum"], list(opencode.AGENT_FORMATS))
        for key, kind in config.LAYERED_KEYS["harnesses"].items():
            want = "boolean" if kind is bool else "string"
            self.assertEqual(harness["properties"][key]["type"], want, key)

    def test_server_forms(self):
        s = schema.load("mcp-servers.toml")
        ok = {"servers": {"a": {"command": "npx", "args": ["x"], "env_from": ["TOKEN"]},
                          "b": {"url": "https://example.com/mcp", "harnesses": ["claude"]}}}
        self.assertEqual(schema.errors(ok, s), [])
        self.assertEqual(schema.errors({"servers": {"a": {"url": "https://e", "env_from": []}}}, s), [])
        for bad in ({"command": "x", "url": "https://e"}, {"url": "https://e", "args": ["x"]},
                    {"url": "https://e", "env_from": ["T"]}, {}, {"command": "x", "env": {"T": "v"}},
                    {"command": "x", "env_from": ["not a name"]}):
            with self.subTest(bad=bad):
                self.assertNotEqual(schema.errors({"servers": {"a": bad}}, s), [])

    def test_editor_associations_point_at_real_schemas(self):
        taplo = load_toml(ROOT / ".taplo.toml")
        paths = {r["schema"]["path"] for r in taplo["rule"]}
        for path in paths:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertEqual({Path(p).name for p in paths},
                         {f"{n}.schema.json" for n in (*NEW, "brainrc.toml", "brainrc.lock")})

    def test_the_schema_directive_names_the_published_pack_schema(self):
        url = PACK_SCHEMA.removeprefix("#:schema ")
        self.assertTrue(url.startswith("https://raw.githubusercontent.com/brainrc/brainrc/main/"))
        self.assertTrue((ROOT / url.split("/main/", 1)[1]).is_file())
        for pack in ("pack-acme", "pack-homelab"):
            first = (ROOT / f"examples/{pack}/pack.toml").read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(first, PACK_SCHEMA, pack)
        self.assertTrue(url in (ROOT / "docs/packs.md").read_text(encoding="utf-8"), "docs/packs.md names it")


class ValidatorKeywordsTest(unittest.TestCase):
    def test_minimum(self):
        s = {"type": "integer", "minimum": 0}
        self.assertEqual(schema.errors(3, s), [])
        self.assertEqual(schema.errors(-1, s), ["the file: must be at least 0"])

    def test_unknown_keys_can_be_collected_instead_of_failing(self):
        s = {"type": "object", "additionalProperties": False, "properties": {
            "a": {"type": "object", "additionalProperties": False, "properties": {}}}}
        unknown = []
        self.assertEqual(schema.errors({"b": 1, "a": {"c": 2}}, s, unknown=unknown), [])
        self.assertEqual(unknown, [((), "b"), (("a",), "c")])
        self.assertEqual(schema.errors({"b": 1}, s), ["the file: unknown key `b`"])

    def test_unknown_keys_inside_a_form_are_collected_from_the_form_that_matches(self):
        closed = {"type": "object", "additionalProperties": False}
        s = {"oneOf": [dict(closed, required=["a"], properties={"a": {"type": "string"}}),
                       dict(closed, required=["b"], properties={"b": {"type": "string"}})],
             "anyOf": [dict(closed, properties={"a": {"type": "string"}})]}
        unknown = []
        self.assertEqual(schema.errors({"a": "x", "typo": 1}, s, unknown=unknown), [])
        self.assertEqual(unknown, [((), "typo"), ((), "typo")])
        self.assertNotEqual(schema.errors({"a": "x", "typo": 1}, s), [])

    def test_harness_names_are_any_table_name(self):
        self.assertEqual(schema.errors({"my_IDE": {"enabled": True}}, schema.load("harnesses.toml")), [])
        servers = {"servers": {"a": {"command": "x", "harnesses": ["my_IDE"]}}}
        self.assertEqual(schema.errors(servers, schema.load("mcp-servers.toml")), [])


class PackTomlValidateTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, self.pack)
        shutil.copytree(ROOT / "examples/pack-homelab", self.pack, dirs_exist_ok=True)
        self.toml = self.pack / "pack.toml"

    def validate(self):
        return quiet(brainrc.cmd_validate, str(self.pack))

    def edit(self, old: str, new: str) -> None:
        text = self.toml.read_text()
        self.assertIn(old, text)
        self.toml.write_text(text.replace(old, new))

    def test_a_typo_warns_and_names_the_key_it_is_closest_to(self):
        self.edit('requires_core = ', 'max_always_token = 400\nrequires_core = ')
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("WARN homelab:pack.toml:5: unknown key `max_always_token` (did you mean "
                      "`max_always_tokens`?); brainrc ignores it", out)

    def test_an_unrelated_unknown_key_warns_without_a_guess(self):
        self.edit('requires_core = ', 'colour = "blue"\nrequires_core = ')
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("unknown key `colour`; brainrc ignores it", out)

    def test_a_known_key_of_the_wrong_type_fails(self):
        self.edit('requires_core = ', 'max_always_tokens = "800"\nid = ["homelab/x"]\nrequires_core = ')
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR homelab:pack.toml: max_always_tokens: must be a number", out)
        self.assertIn("must be `<owner>/<pack>`", out)
        self.assertNotIn("id: must be a string", out)  # one error per mistake

    def test_a_decimal_budget_is_still_a_budget(self):
        self.edit('requires_core = ', 'max_always_tokens = 1500.0\nrequires_core = ')
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        from brainrc.sources import load_pack
        from brainrc.tokens import source_budget
        self.assertEqual(source_budget(load_pack(self.pack)), 1500.0)

    def test_apply_still_installs_a_pack_with_a_wrong_type(self):
        from brainrc.sources import load_pack, sources
        from brainrc.validate import pack_errors
        self.edit('requires_core = ', 'description = 1\nrequires_core = ')
        self.assertEqual(dict(pack_errors([*sources(), load_pack(self.pack)])).get("homelab", []), [])
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("homelab:pack.toml: description: must be a string", out)

    def test_a_misspelled_table_header_names_its_line(self):
        text = self.toml.read_text()
        self.toml.write_text(text + '\n[[extension.gatework.domains]]\nfiles = "x"\n')
        line = len(text.splitlines()) + 2
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn(f"WARN homelab:pack.toml:{line}: unknown key `extension` (did you mean `extensions`?)", out)

    def test_a_negative_budget_fails(self):
        self.edit('requires_core = ', 'max_always_tokens = -1\nrequires_core = ')
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR homelab:pack.toml: max_always_tokens: must be at least 0", out)

    def test_extensions_must_be_a_table(self):
        self.toml.write_text('extensions = "x"\n' + self.toml.read_text())
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("homelab:pack.toml: extensions: must be an object", out)

    def test_the_shipped_examples_have_no_pack_toml_findings(self):
        for pack in ("pack-acme", "pack-homelab"):
            with self.subTest(pack=pack):
                _, out = quiet(brainrc.cmd_validate, str(ROOT / "examples" / pack))
                self.assertNotIn(":pack.toml:", out)


class ScaffoldedPackTest(TempRepoCase):
    """What the importers write (brainrc/scaffold.py, E12) passes the stricter validate."""

    def test_a_full_spec_passes_with_no_warnings_about_pack_toml(self):
        dest = Path(tempfile.mkdtemp()).resolve() / "team"
        self.addCleanup(rmtree, dest.parent)
        spec = PackSpec("team", description="Team rules", rules=[Rule("git", "# Git\n\nRebase.")],
                        skills=[Skill("proto", "Protocol Buffers. Use for *.proto.", "Body.")],
                        domains=[{"files": "`*.proto`", "skills": ["team-proto"]}])
        write_pack(dest, render_pack(spec))
        self.assertEqual(render_pack(spec)["pack.toml"].splitlines()[0], PACK_SCHEMA)
        code, out = quiet(brainrc.cmd_validate, str(dest))
        self.assertEqual(code, 0, out)
        self.assertNotIn("team:pack.toml:", out)


if __name__ == "__main__":
    unittest.main()
