"""The pack API version (#174): packs pin `requires_api`, which core content releases never break,
and the frozen contract fails the tests when it changes without PACK_API moving."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import PACK_TOML, TempRepoCase, brainrc, make_pack, quiet, set_core_version  # noqa: E402
from brainrc import packapi  # noqa: E402
from support import rmtree  # noqa: E402

API_PACK_TOML = PACK_TOML.replace('requires_core = ">=1.0, <2"\n', 'requires_api = "^1"\n')


class FrozenContractTest(unittest.TestCase):
    def test_the_live_contract_is_the_frozen_one(self):
        self.assertEqual(packapi.check(), [])

    def test_pack_api_is_frozen_and_pinnable(self):
        self.assertIn(packapi.PACK_API, packapi.FROZEN)
        self.assertEqual(json.loads(packapi.frozen_path(packapi.PACK_API).read_text())["pack_api"], packapi.PACK_API)

    def test_the_contract_covers_what_packs_rely_on(self):
        entries = packapi.contract()
        for expected in ('pack.toml requires_api: type "string"', 'pack.toml guard.deny[]: requires reason',
                         "kind skills", "layout mcp/servers.toml", "validator render_extensions",
                         'mcp/servers.toml servers.*.command: type "string"'):
            self.assertIn(expected, entries)
        self.assertFalse([e for e in entries if "description" in e and "frontmatter" not in e
                          and e != 'pack.toml description: type "string"'], "descriptions are prose, not contract")

    def test_validator_calls_and_schema_combinators_are_in_it(self):
        entries = packapi.contract()
        self.assertIn("validator check_extensions(4 arguments)", entries)
        self.assertIn("validator REMOVED_IN", entries)
        self.assertTrue(any(e.startswith("mcp/servers.toml servers.*: oneOf ") for e in entries))
        self.assertIn("pack.toml .: additionalProperties false", entries)

    def test_one_more_argument_for_a_validator_changes_the_contract(self):
        text = 'x = _call(me, mod, "doctor", me, extra(a, b))\nhasattr(mod, "NAMESPACE")\n'
        self.assertEqual(packapi._validator_entries(text), {"validator doctor(2 arguments)", "validator NAMESPACE"})

    def test_write_refuses_a_released_version(self):
        before = packapi.frozen_path(packapi.PACK_API).read_text(encoding="utf-8")
        code, out = quiet(packapi.main, ["--write"])
        self.assertEqual(code, 1)
        self.assertIn("already frozen; bump PACK_API first", out)
        self.assertEqual(packapi.frozen_path(packapi.PACK_API).read_text(encoding="utf-8"), before)

    def test_a_contract_change_without_a_version_bump_fails(self):
        with mock.patch.object(packapi, "LAYOUT", (*packapi.LAYOUT, "hooks.toml")):
            problems = packapi.check()
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("the pack contract changed but PACK_API is still 1.0", problems[0])
        self.assertIn("added ['layout hooks.toml']", problems[0])
        self.assertIn("python3 scripts/pack_api.py --write", problems[0])

    def test_a_removed_entry_fails_too(self):
        with mock.patch.object(packapi, "LAYOUT", packapi.LAYOUT[1:]):
            problems = packapi.check()
        self.assertIn("removed ['layout pack.toml']", problems[0])

    def test_an_edited_frozen_file_fails(self):
        with mock.patch.dict(packapi.FROZEN, {"1.0": "0" * 64}):
            problems = packapi.check()
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("docs/schemas/pack-api/1.0.json changed, but a released "
                                               "pack API never changes: restore it, then bump PACK_API"), problems)


class VersionHistoryTest(unittest.TestCase):
    """Bumps across frozen files, in a temp folder: MINOR keeps every entry, MAJOR may drop some."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp()).resolve()
        live = packapi.contract()
        self.versions = {"1.0": live[1:], "1.1": live}
        self.addCleanup(rmtree, self.dir)

    def check(self, versions: dict[str, list[str]], current: str) -> list[str]:
        frozen = {}
        for version, entries in versions.items():
            text = packapi.render(version, entries)
            (self.dir / f"{version}.json").write_text(text)
            frozen[version] = packapi.digest(text)
        with mock.patch.object(packapi, "frozen_path", lambda v: self.dir / f"{v}.json"), \
             mock.patch.object(packapi, "FROZEN", frozen), mock.patch.object(packapi, "PACK_API", current):
            return packapi.check()

    def test_a_minor_bump_that_adds_passes(self):
        self.assertEqual(self.check(self.versions, "1.1"), [])

    def test_a_minor_bump_that_drops_fails(self):
        live = packapi.contract()
        problems = self.check({"1.0": live + ["layout gone.toml"], "1.1": live}, "1.1")
        self.assertEqual(problems, ["pack API 1.1 drops what 1.0 promised, so it needs a MAJOR bump: "
                                    "['layout gone.toml']"])

    def test_a_major_bump_may_drop(self):
        live = packapi.contract()
        self.assertEqual(self.check({"1.0": live + ["layout gone.toml"], "2.0": live}, "2.0"), [])

    def test_pack_api_must_be_the_newest(self):
        self.assertEqual(self.check(self.versions, "1.0"), ["PACK_API is 1.0, but FROZEN goes up to 1.1"])

    def test_a_frozen_file_needs_a_digest(self):
        (self.dir / "0.9.json").write_text("{}")
        self.assertIn("docs/schemas/pack-api/0.9.json has no digest in FROZEN", self.check(self.versions, "1.1"))


class RequiresApiTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack", API_PACK_TOML)
        self.addCleanup(rmtree, self.pack.parent)

    def pin(self, line: str) -> None:
        toml = self.pack / "pack.toml"
        toml.write_text(toml.read_text().replace('requires_api = "^1"\n', line + "\n"))

    def test_a_pin_survives_core_content_releases(self):
        for version in ("0.8.40", "0.9.0", "1.4.2", "2.0.0"):
            set_core_version(self.repo, version)
            with self.subTest(core=version):
                code, out = quiet(brainrc.cmd_validate, str(self.pack))
                self.assertEqual(code, 0, out)
                self.assertNotIn("requires_", out)

    def test_another_major_fails(self):
        self.pin('requires_api = "^2"')
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:pack.toml: requires_api `^2` is not satisfied by pack API 1.0", out)

    def test_a_malformed_pin_fails(self):
        self.pin('requires_api = "one"')
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:pack.toml: invalid requires_api `one`", out)

    def test_requires_core_beside_it_is_left_for_older_cores(self):
        self.pin('requires_api = "^1"\nrequires_core = ">=0.8, <0.9"')
        set_core_version(self.repo, "0.9.0")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertNotIn("requires_", out)

    def test_requires_core_alone_still_works_and_only_its_author_hears_it_is_deprecated(self):
        self.pin('requires_core = ">=0.8, <0.9"')
        set_core_version(self.repo, "0.9.0")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)  # still enforced while deprecated
        self.assertIn("requires_core `>=0.8, <0.9` is not satisfied by core 0.9.0", out)
        set_core_version(self.repo, "0.8.40")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN acme:pack.toml: `requires_core` is deprecated", out)
        (self.repo / "packs.local.toml").write_text(f"[acme]\npath = '{self.pack}'\n")
        code, out = quiet(brainrc.cmd_validate)  # core's own validate: the pack's users can't fix it
        self.assertIn("(packs: gatework, acme)", out)
        self.assertNotIn("deprecated", out)


if __name__ == "__main__":
    unittest.main()
