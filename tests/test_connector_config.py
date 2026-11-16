"""Connector config schema (#136): a connector skill declares its config keys and types in SKILL.md
`metadata`, validate checks every pack table that names it, and `instructions` is a defined field
the pack's tripwires check."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet  # noqa: E402
from brainrc import config, connectors  # noqa: E402
from brainrc.connectors import Field  # noqa: E402
from brainrc.validate import pack_errors  # noqa: E402
from brainrc.sources import load_pack, sources  # noqa: E402
from support import rmtree  # noqa: E402


EXAMPLE_INSTRUCTIONS = 'instructions = "Link the PR in the ticket\'s Development panel, not in a comment."'


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class DeclarationTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(rmtree, self.dir)

    def skill(self, front: str) -> Path:
        write(self.dir / "s/SKILL.md", f"---\nname: s\ndescription: d\n{front}---\nBody.\n")
        return self.dir / "s"

    def test_metadata_reads_plain_and_quoted_values_and_stops_at_the_next_key(self):
        s = self.skill('metadata:\n  brainrc-config: "a: string; b: list required"  # c\n'
                       "  other: plain value # comment\nlicense: MIT\n  stray: x\n")
        self.assertEqual(connectors.metadata(s / "SKILL.md"),
                         {"brainrc-config": "a: string; b: list required", "other": "plain value"})
        self.assertEqual(connectors.declared(s), {"a": Field("string"), "b": Field("list", True)})

    def test_metadata_reads_wrapped_and_block_values_and_skips_nested_maps(self):
        s = self.skill('metadata:\n  brainrc-config: "refs: list required;\n    host: string required"\n'
                       "  folded: >-\n    one\n    two\n  kept: |\n    a\n    b\n"
                       "  owner:\n    brainrc-config: nested\n  plain: wraps\n    on\n")
        self.assertEqual(connectors.metadata(s / "SKILL.md"), {
            "brainrc-config": "refs: list required; host: string required", "folded": "one two",
            "kept": "a\nb", "owner": "brainrc-config: nested", "plain": "wraps on"})
        self.assertEqual(connectors.declared(s), {"refs": Field("list", True), "host": Field("string", True)})

    def test_a_broken_declaration_declares_nothing(self):
        self.assertIsNone(connectors.declared(self.skill('metadata:\n  brainrc-config: "a: string; b: str"\n')))

    def test_no_metadata_means_no_declaration(self):
        self.assertIsNone(connectors.declared(self.skill("")))
        write(self.dir / "t/SKILL.md", "no frontmatter\nmetadata:\n  brainrc-config: a: string\n")
        self.assertIsNone(connectors.declared(self.dir / "t"))

    def test_parse_names_each_bad_entry(self):
        fields, problems = connectors.parse("a: string; b: number; c; a: list; connector: string; d: boolean required;")
        self.assertEqual(fields, {"a": Field("string"), "d": Field("boolean", True)})
        self.assertEqual(len(problems), 4, problems)
        self.assertIn("`b: number` must be `key: type`", problems[0])
        self.assertIn("`a` is declared twice", problems[2])
        self.assertIn("`connector` is set for every connector", problems[3])

    def test_tables_finds_namespaced_and_legacy_connector_tables(self):
        meta = {"extensions": {"gatework": {"ticket": {"connector": "x"}, "domains": [{"connector": "no"}]},
                               "ticket": {"connector": "y"}, "deliver_checks": ["z"]}}
        self.assertEqual(connectors.tables(meta), [("extensions.gatework.ticket", {"connector": "x"}),
                                                   ("extensions.ticket", {"connector": "y"})])
        self.assertEqual(connectors.tables({"extensions": "x"}), [])


class KeyLineTest(unittest.TestCase):
    TEXT = ('#:schema x\nname = "acme"\nmax_always_token = 4\n[extensions.gatework]\nticket.host = "h"\n'
            "ticket.blocked_stat = 1\n[[extension.gatework.domains]]\nfiles = 1\n[extensions.gatework.other]\nkey = 2\n")

    def test_each_form_of_key(self):
        for path, line in [(("max_always_token",), 3), (("extensions", "gatework", "ticket", "blocked_stat"), 6),
                           (("extension",), 7), (("extensions", "gatework", "other", "key"), 10),
                           (("missing",), 1)]:
            with self.subTest(path=path):
                self.assertEqual(config.key_line(self.TEXT, path), line)


class ValidateTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, self.pack)
        shutil.copytree(ROOT / "examples/pack-acme", self.pack, dirs_exist_ok=True)
        self.toml = self.pack / "pack.toml"

    def validate(self):
        return quiet(brainrc.cmd_validate, str(self.pack))

    def edit(self, old: str, new: str) -> None:
        text = self.toml.read_text()
        self.assertIn(old, text)
        self.toml.write_text(text.replace(old, new))

    def test_the_example_pack_matches_its_connector(self):
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertNotIn("brainrc-ticket-jira", out)

    def test_a_bad_key_type_fails(self):
        self.edit('host = "acme.example.net"', "host = 3")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR acme:pack.toml: [extensions.gatework.ticket] `host` must be a string "
                      "(brainrc-ticket-jira's config)", out)

    def test_a_missing_required_key_and_a_list_of_numbers_fail(self):
        self.edit('host = "acme.example.net"\n', "")
        self.edit('refs = ["ACME-*"]', "refs = [1]")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("[extensions.gatework.ticket] needs `host` (brainrc-ticket-jira's config)", out)
        self.assertIn("[extensions.gatework.ticket] `refs` must be a list of strings", out)

    def test_apply_still_installs_the_pack(self):
        # Like pack.toml's schema, connector config is validate's to report; apply goes ahead.
        self.edit('host = "acme.example.net"', "host = true")
        srcs = [*sources(), load_pack(self.pack)]
        self.assertNotIn("acme", dict((s.name, e) for s, e in pack_errors(srcs)))

    def test_an_unknown_key_warns_with_the_closest_declared_one(self):
        self.edit('review_status = "In Review"', 'review_status = "In Review"\nblocked_stat = "Blocked"')
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"WARN acme:pack\.toml:\d+: \[extensions\.gatework\.ticket\] unknown key "
                              r"`blocked_stat` for brainrc-ticket-jira \(did you mean `blocked_status`\?\)")

    def test_notes_warns_that_it_is_now_instructions(self):
        self.edit('review_status = "In Review"', 'review_status = "In Review"\nnotes = "Use the API"')
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("unknown key `notes` for brainrc-ticket-jira; it is now `instructions`", out)

    def test_instructions_must_be_a_string_and_need_no_declaration(self):
        code, out = self.validate()  # the example sets it
        self.assertEqual(code, 0, out)
        self.assertNotIn("instructions", out)
        self.edit(EXAMPLE_INSTRUCTIONS, "instructions = 1")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("[extensions.gatework.ticket] `instructions` must be a string", out)

    def test_tripwires_check_instructions(self):
        self.edit(EXAMPLE_INSTRUCTIONS, 'instructions = """\nLink the PR.\nPage on-call with pagerbot.\n"""')
        write(self.pack / "tripwires.toml", '[[tripwire]]\nid = "old-pager"\npattern = "(?i)pagerbot"\n'
                                            'message = "pagerbot was replaced"\n')
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"ERROR acme:pack\.toml:\d+: \[extensions\.gatework\.ticket\] instructions: "
                              r"tripwire old-pager: pagerbot was replaced")

    def test_the_instructions_tripwire_follows_paths_and_exclude(self):
        self.edit(EXAMPLE_INSTRUCTIONS, 'instructions = "Page on-call with pagerbot."')
        base = '[[tripwire]]\nid = "old-pager"\npattern = "(?i)pagerbot"\nmessage = "gone"\n'
        for extra, count in (('paths = ["*.toml"]\n', 1), ('paths = ["skills/*"]\n', 0),
                             ('exclude = ["pack.toml"]\n', 0)):
            with self.subTest(extra=extra):
                write(self.pack / "tripwires.toml", base + extra)
                _, out = self.validate()
                self.assertEqual(out.count("tripwire old-pager"), count, out)

    def test_a_connector_without_a_declaration_is_not_checked(self):
        self.edit('connector = "brainrc-ticket-jira"', 'connector = "brainrc-ticket-github"')
        self.edit('host = "acme.example.net"', "host = 3")
        code, out = self.validate()
        self.assertEqual(code, 0, out)

    def test_the_packs_own_connector_and_its_declaration(self):
        write(self.pack / "skills/acme-ticket-desk/SKILL.md",
              "---\nname: acme-ticket-desk\ndescription: Ticket connector for the desk. Use for DESK refs.\n"
              'metadata:\n  brainrc-config: "refs: list required; queue: integer; tier: colour"\n---\nBody.\n')
        self.edit('connector = "brainrc-ticket-jira"', 'connector = "acme-ticket-desk"')
        self.edit('host = "acme.example.net"', 'queue = "7"')
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("acme:skills/acme-ticket-desk/SKILL.md: metadata.brainrc-config: `tier: colour` must be", out)
        self.assertNotIn("acme-ticket-desk's config", out)  # a broken declaration checks no pack
        skill = self.pack / "skills/acme-ticket-desk/SKILL.md"
        skill.write_text(skill.read_text().replace("; tier: colour", ""))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("`queue` must be an integer (acme-ticket-desk's config)", out)

    def test_the_legacy_top_level_table_is_checked_too(self):
        text = self.toml.read_text().replace("[extensions.gatework.ticket]", "[extensions.ticket]")
        self.toml.write_text(text.replace('host = "acme.example.net"', "host = 3"))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("[extensions.ticket] `host` must be a string", out)


if __name__ == "__main__":
    unittest.main()
