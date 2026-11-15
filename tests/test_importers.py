"""`brainrc import` (E12, #118): instruction files from other tools become a pack that validates."""
import os
import re
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import REPO, TempRepoCase, brainrc, quiet  # noqa: E402

from brainrc.importers import discover, plan, resolve, set_pack_path  # noqa: E402
from brainrc.importers.markdown import headings, split  # noqa: E402
from brainrc.scaffold import PackSpec, Rule, Skill, render_pack, write_pack  # noqa: E402
from brainrc.sources import Source, load_pack, render_instructions, sources  # noqa: E402
from support import rmtree  # noqa: E402

FIXTURES = REPO / "tests/fixtures/import"
COMMENT = re.compile(r"<!-- .*? -->\n*")


def normalized(text: str) -> str:
    """Text as rendered rules carry it: no trailing spaces, at most one blank line in a row."""
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))


def rendered_pack_text(pack: Path) -> str:
    """The pack's part of the instructions file, without the comments brainrc adds."""
    src = load_pack(pack)
    text = render_instructions([Source("core", brainrc.config.REPO), src])
    after_label = text.split(f"<!-- pack: {src.name} -->\n", 1)[1].split("\n", 1)[1]  # drop its sentence
    return COMMENT.sub("", after_label)


class SplitTest(unittest.TestCase):
    def test_splits_at_the_shallowest_level_used_twice(self):
        text = "# Title\n\nIntro.\n\n## A\n\nOne.\n\n### A.1\n\nDeep.\n\n## B\n\nTwo.\n"
        self.assertEqual([(s.title, s.first, s.last) for s in split(text)],
                         [("Title", 1, 3), ("A", 5, 11), ("B", 13, 15)])

    def test_text_without_headings_is_one_section(self):
        [section] = split("\n\nJust a paragraph.\nAnd a second line.\n\n")
        self.assertEqual((section.title, section.first, section.last), ("", 3, 4))
        self.assertEqual(section.text, "Just a paragraph.\nAnd a second line.")

    def test_headings_inside_code_fences_do_not_count(self):
        text = "## A\n\n```sh\n# comment\n## also a comment\n```\n\n~~~\n# x\n~~~\n## B\n"
        self.assertEqual([t for _, _, t in headings(text.splitlines())], ["A", "B"])

    def test_a_longer_fence_closes_only_on_a_long_enough_line(self):
        text = "````\n```\n# inside\n```\n````\n# outside\n"
        self.assertEqual([t for _, _, t in headings(text.splitlines())], ["outside"])

    def test_empty_text_has_no_sections(self):
        self.assertEqual(split("\n  \n"), [])


class ScaffoldTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        rmtree(self.tmp)

    def test_rule_files_keep_their_order_past_nine(self):
        files = render_pack(PackSpec("team", rules=[Rule(f"r{i}", f"Rule {i}.") for i in range(12)]))
        names = [p for p in files if p.startswith("rules/")]
        self.assertEqual(names[:2], ["rules/01-r0.md", "rules/02-r1.md"])
        self.assertEqual(names, sorted(names))
        few = render_pack(PackSpec("team", rules=[Rule("a", "A."), Rule("b", "B.")]))
        self.assertIn("rules/10-a.md", few)
        self.assertIn("rules/20-b.md", few)

    def test_provenance_is_a_comment_on_the_first_line(self):
        files = render_pack(PackSpec("team", rules=[Rule("a", "Text.", "imported -- from x")]))
        self.assertEqual(files["rules/10-a.md"], "<!-- imported - - from x -->\n\nText.\n")

    def test_skills_get_the_prefix_and_a_quoted_description(self):
        files = render_pack(PackSpec("team", prefix="tm-", skills=[Skill("api", 'Use for "api"\n files.', "Body.")]))
        text = files["skills/tm-api/SKILL.md"]
        self.assertTrue(text.startswith('---\nname: tm-api\ndescription: "Use for \\"api\\" files."\n---\n'))

    def test_pack_toml_parses_and_names_this_core(self):
        files = render_pack(PackSpec("team", description='Has "quotes"', domains=[
            {"files": "`src/**/*.ts`", "skills": ["team-ts"]}]))
        meta = tomllib.loads(files["pack.toml"])
        self.assertEqual(meta["name"], "team")
        self.assertEqual(meta["prefix"], "team-")
        self.assertEqual(meta["description"], 'Has "quotes"')
        self.assertTrue(meta["requires_core"].startswith(">="))
        self.assertEqual(meta["extensions"]["gatework"]["domains"],
                         [{"files": "`src/**/*.ts`", "skills": ["team-ts"]}])

    def test_bad_names_are_refused_before_anything_is_written(self):
        for name, prefix in (("Team", ""), ("team", "t-"), ("team", "team")):
            with self.assertRaises(brainrc.config.ConfigError):
                render_pack(PackSpec(name, prefix))

    def test_write_refuses_a_folder_with_files_unless_forced(self):
        dest = self.tmp / "pack"
        write_pack(dest, {"pack.toml": 'name = "a"\n'})
        with self.assertRaises(brainrc.config.ConfigError):
            write_pack(dest, {"pack.toml": 'name = "b"\n'})
        self.assertEqual((dest / "pack.toml").read_text(), 'name = "a"\n')
        write_pack(dest, {"pack.toml": 'name = "b"\n', "rules/10-x.md": "X.\n"}, force=True)
        self.assertEqual((dest / "pack.toml").read_text(), 'name = "b"\n')
        self.assertEqual([p.name for p in self.tmp.iterdir()], ["pack"])  # no temp dir left behind

    def test_write_refuses_paths_outside_the_folder(self):
        for rel in ("../escape.md", "/abs.md"):
            with self.assertRaises(brainrc.config.ConfigError):
                write_pack(self.tmp / "pack", {rel: "x"})
        self.assertFalse((self.tmp / "pack").exists())


class ImportCase(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.old_cwd)
        rmtree(self.tmp)
        super().tearDown()

    def run_import(self, *args: str) -> tuple[int, str]:
        return quiet(brainrc.cli.main, ["brainrc", "import", *args])


class InstructionsImportTest(ImportCase):
    """#163: CLAUDE.md and AGENTS.md."""

    def test_agents_md_imports_into_a_pack_that_validates_and_renders_the_same_text(self):
        source = FIXTURES / "instructions/AGENTS.md"
        code, out = self.run_import(str(source), "--to", "team", "--name", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("OK:", out)
        pack = self.tmp / "team"
        self.assertEqual(sorted(p.name for p in (pack / "rules").iterdir()),
                         ["10-team-conventions.md", "20-git.md", "30-testing.md", "40-review.md"])
        self.assertEqual(rendered_pack_text(pack).strip(), normalized(source.read_text()))

    def test_every_rule_names_its_file_and_lines(self):
        source = FIXTURES / "instructions/AGENTS.md"
        self.assertEqual(self.run_import(str(source), "--to", "team")[0], 0)
        lines = source.read_text().splitlines()
        for rule in sorted((self.tmp / "team/rules").iterdir()):
            first, body = rule.read_text().split("\n\n", 1)
            m = re.fullmatch(r"<!-- imported by brainrc from (.+), lines (\d+)-(\d+) -->", first)
            self.assertIsNotNone(m, first)
            self.assertEqual(m[1], brainrc.config.tilde(source))
            a, b = int(m[2]), int(m[3])
            self.assertEqual(body.strip(), "\n".join(lines[a - 1:b]))

    def test_claude_md_inlines_its_imports_in_place_and_drops_the_brainrc_block(self):
        code, out = self.run_import(str(FIXTURES / "instructions/CLAUDE.md"), "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("`@missing.md` not inlined (no such file); kept as text", out)
        text = rendered_pack_text(self.tmp / "team")
        order = ["Be concise.", "# Team conventions", "## Git", "### Flaky tests", "## Review",
                 "@missing.md", "## Claude Code only"]
        self.assertEqual([text.index(s) for s in order], sorted(text.index(s) for s in order))
        self.assertNotIn("brainrc:begin", text)
        self.assertNotIn(".brainrc/AGENTS.md", text)
        rules = sorted((self.tmp / "team/rules").iterdir())
        self.assertIn("instructions/CLAUDE.md, lines 1-1", rules[0].read_text())
        self.assertIn("instructions/AGENTS.md, lines 1-3", rules[1].read_text())

    def test_a_folder_imports_claude_md_and_skips_the_agents_md_it_already_inlined(self):
        code, out = self.run_import(str(FIXTURES / "instructions"), "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("AGENTS.md: already imported through an @import above; skipped", out)
        self.assertEqual(rendered_pack_text(self.tmp / "team").count("## Git"), 1)

    def test_an_import_cycle_is_kept_as_text(self):
        (self.tmp / "a").mkdir()
        (self.tmp / "a/CLAUDE.md").write_text("Top.\n\n@AGENTS.md\n")
        (self.tmp / "a/AGENTS.md").write_text("Agents.\n\n@CLAUDE.md\n")
        code, out = self.run_import("a/CLAUDE.md", "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("`@CLAUDE.md` imports itself; kept as text", out)

    def test_dry_run_writes_nothing(self):
        code, out = self.run_import(str(FIXTURES / "instructions/AGENTS.md"), "--dry-run", "--enable")
        self.assertEqual(code, 0, out)
        self.assertIn("would write rules/10-team-conventions.md", out)
        self.assertIn("5 files: 4 rules, 0 skills", out)
        self.assertFalse(self.settings_home.exists() and any(self.settings_home.rglob("*")))
        self.assertFalse((self.repo / "packs.local.toml").exists())

    def test_enable_adds_the_pack_and_apply_sources_it(self):
        code, out = self.run_import(str(FIXTURES / "instructions/AGENTS.md"), "--enable", "--name", "team")
        self.assertEqual(code, 0, out)
        dest = self.settings_home / "imported/team"
        self.assertTrue((dest / "pack.toml").is_file())
        packs = tomllib.loads((self.repo / "packs.local.toml").read_text())
        self.assertEqual(brainrc.config.expand(packs["team"]["path"]), dest)
        self.assertIn("team", [s.name for s in sources()])
        self.assertIn("## Testing", render_instructions(sources()))

    def test_an_existing_pack_folder_is_not_overwritten(self):
        self.assertEqual(self.run_import(str(FIXTURES / "instructions/AGENTS.md"), "--to", "team")[0], 0)
        code, out = self.run_import(str(FIXTURES / "instructions/CLAUDE.md"), "--to", "team")
        self.assertEqual(code, 1)
        self.assertIn("already has files", out)
        self.assertEqual(self.run_import(str(FIXTURES / "instructions/CLAUDE.md"), "--to", "team", "--force")[0], 0)

    def test_unknown_and_empty_sources_fail_without_writing(self):
        (self.tmp / "notes.txt").write_text("hi\n")
        (self.tmp / "empty").mkdir()
        (self.tmp / "empty/AGENTS.md").write_text("\n")
        for args, message in ((["notes.txt"], "not a format brainrc imports"),
                              (["nowhere.md"], "no such file or folder"),
                              (["empty/AGENTS.md"], "nothing to import")):
            code, out = self.run_import(*args, "--to", "team")
            self.assertEqual(code, 1, out)
            self.assertIn(message, out)
        self.assertFalse((self.tmp / "team").exists())

    def test_format_reads_any_markdown_file_as_instructions(self):
        (self.tmp / "conventions.md").write_text("## One\n\nA.\n\n## Two\n\nB.\n")
        code, out = self.run_import("conventions.md", "--format", "instructions", "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(list((self.tmp / "team/rules").iterdir())), 2)

    def test_discover_and_resolve(self):
        self.assertEqual([(f, p.name) for f, p in discover(FIXTURES / "instructions")],
                         [("instructions", "CLAUDE.md"), ("instructions", "AGENTS.md")])
        p = plan(resolve([str(FIXTURES / "instructions/AGENTS.md")]), "team")
        self.assertEqual(p.spec.description, "Imported by brainrc import from AGENTS.md")


class SetPackPathTest(unittest.TestCase):
    def test_new_table(self):
        self.assertEqual(set_pack_path("", "team", "~/p"), '[team]\npath = "~/p"\n')
        self.assertEqual(set_pack_path("# mine\n", "team", "~/p"), '# mine\n\n[team]\npath = "~/p"\n')

    def test_replaces_the_tables_origin_and_keeps_the_rest(self):
        text = '[team]\ngit = "https://x"\nref = "v1"\nenabled = false\n\n[other]\npath = "~/o"\n'
        after = set_pack_path(text, "team", "~/p")
        self.assertEqual(tomllib.loads(after), {"team": {"path": "~/p", "enabled": False},
                                                "other": {"path": "~/o"}})


if __name__ == "__main__":
    unittest.main()
