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
from brainrc.importers.markdown import globs, headings, split  # noqa: E402
from brainrc.scaffold import PackSpec, Rule, Skill, render_pack, write_pack  # noqa: E402
from brainrc.sources import Source, frontmatter, load_pack, render_instructions, sources  # noqa: E402
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

    def test_force_replaces_only_an_earlier_pack(self):
        dest = self.tmp / "work"
        dest.mkdir()
        (dest / "notes.md").write_text("mine\n")
        with self.assertRaisesRegex(brainrc.config.ConfigError, "no pack.toml"):
            write_pack(dest, {"pack.toml": "x\n"}, force=True)
        self.assertEqual((dest / "notes.md").read_text(), "mine\n")

    def test_force_never_replaces_a_folder_that_holds_a_source(self):
        dest = self.tmp / "pack"
        write_pack(dest, {"pack.toml": "a\n", "AGENTS.md": "src\n"})
        with self.assertRaisesRegex(brainrc.config.ConfigError, "being imported"):
            write_pack(dest, {"pack.toml": "b\n"}, force=True, sources=[dest / "AGENTS.md"])
        self.assertEqual((dest / "AGENTS.md").read_text(), "src\n")

    def test_a_link_is_not_written_through(self):
        target = self.tmp / "elsewhere"
        target.mkdir()
        (self.tmp / "pack").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(brainrc.config.ConfigError, "a link"):
            write_pack(self.tmp / "pack", {"pack.toml": "x\n"}, force=True)
        self.assertEqual(list(target.iterdir()), [])

    def test_write_refuses_paths_outside_the_folder(self):
        for rel in ("../escape.md", "/abs.md", "C:/abs.md", "a\\..\\..\\b.md", "\\abs.md"):
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
        first = sorted((self.tmp / "team/rules").iterdir())[0].read_text()
        claude, agents = (brainrc.config.tilde(FIXTURES / "instructions" / n) for n in ("CLAUDE.md", "AGENTS.md"))
        self.assertTrue(first.startswith(f"<!-- imported by brainrc from {claude}, lines 1-2; {agents}, lines 1-3 -->"))

    def test_a_folder_imports_claude_md_and_skips_the_agents_md_it_already_inlined(self):
        code, out = self.run_import(str(FIXTURES / "instructions"), "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("AGENTS.md: already imported with", out)
        self.assertEqual(rendered_pack_text(self.tmp / "team").count("## Git"), 1)

    def test_an_import_cycle_is_kept_as_text(self):
        (self.tmp / "a").mkdir()
        (self.tmp / "a/CLAUDE.md").write_text("Top.\n\n@AGENTS.md\n")
        (self.tmp / "a/AGENTS.md").write_text("Agents.\n\n@CLAUDE.md\n")
        code, out = self.run_import("a/CLAUDE.md", "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("`@CLAUDE.md` not inlined (imports itself); kept as text", out)

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

    def test_skip_does_not_depend_on_source_order(self):
        for order in (("AGENTS.md", "CLAUDE.md"), ("CLAUDE.md", "AGENTS.md")):
            p = plan(resolve([str(FIXTURES / "instructions" / n) for n in order]), "team")
            self.assertEqual([path.name for _, path in p.sources], ["CLAUDE.md"], order)
            self.assertEqual(sum(r.text.count("## Git") for r in p.spec.rules), 1)

    def test_an_import_in_the_middle_of_a_section_splits_as_one_text(self):
        (self.tmp / "a").mkdir()
        (self.tmp / "a/part.md").write_text("Inlined line.\n")
        (self.tmp / "a/CLAUDE.md").write_text("## One\n\nBefore.\n@part.md\nAfter.\n\n## Two\n\nB.\n")
        p = plan(resolve(["a/CLAUDE.md"]), "team")
        self.assertEqual([r.slug for r in p.spec.rules], ["one", "two"])
        self.assertIn("Before.\nInlined line.\nAfter.", p.spec.rules[0].text)

    def test_an_import_inside_a_fence_stays_as_text(self):
        (self.tmp / "a").mkdir()
        (self.tmp / "a/part.md").write_text("Inlined.\n")
        (self.tmp / "a/CLAUDE.md").write_text("Use:\n\n```\n@part.md\n```\n")
        p = plan(resolve(["a/CLAUDE.md"]), "team")
        self.assertIn("@part.md", p.spec.rules[0].text)
        self.assertNotIn("Inlined.", p.spec.rules[0].text)

    def test_format_with_a_folder_reads_that_formats_sources_in_it(self):
        code, out = self.run_import(str(FIXTURES), "--format", "instructions", "--to", "team")
        self.assertEqual(code, 1, out)
        self.assertIn("no instructions sources in it", out)
        code, out = self.run_import(str(FIXTURES / "cursor"), "--format", "cursor", "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("Import", out)

    def test_a_source_that_is_not_utf8_fails_cleanly(self):
        (self.tmp / "AGENTS.md").write_bytes(b"## A\n\ncaf\xe9\n")
        code, out = self.run_import("AGENTS.md", "--to", "team")
        self.assertEqual(code, 1, out)
        self.assertIn("isn't UTF-8", out)
        self.assertNotIn("Traceback", out)
        self.assertFalse((self.tmp / "team").exists())

    def test_enable_turns_on_a_pack_that_was_off(self):
        (self.repo / "packs.local.toml").write_text('[team]\npath = "~/old"\nenabled = false\n')
        code, out = self.run_import(str(FIXTURES / "instructions/AGENTS.md"), "--enable", "--name", "team")
        self.assertEqual(code, 0, out)
        self.assertNotIn("enabled", (self.repo / "packs.local.toml").read_text())
        self.assertIn("team", [s.name for s in sources()])

    def test_enable_reports_a_broken_packs_file(self):
        (self.repo / "packs.local.toml").write_text("[team\n")
        code, out = self.run_import(str(FIXTURES / "instructions/AGENTS.md"), "--enable", "--name", "team")
        self.assertEqual(code, 1, out)
        self.assertIn("invalid TOML", out)

    def test_discover_and_resolve(self):
        self.assertEqual([(f, p.name) for f, p in discover(FIXTURES / "instructions")],
                         [("instructions", "CLAUDE.md"), ("instructions", "AGENTS.md")])
        p = plan(resolve([str(FIXTURES / "instructions/AGENTS.md")]), "team")
        self.assertEqual(p.spec.description, "Imported by brainrc import from AGENTS.md")


class CursorImportTest(ImportCase):
    """#164: `.cursor/rules/*.mdc` and `.cursorrules`."""

    def import_fixture(self) -> Path:
        code, out = self.run_import(str(FIXTURES / "cursor"), "--to", "team", "--name", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("OK:", out)
        self.assertNotIn("ERROR", out)
        return self.tmp / "team"

    def test_always_apply_rules_become_rules_in_order(self):
        pack = self.import_fixture()
        self.assertEqual(sorted(p.name for p in (pack / "rules").iterdir()),
                         ["10-general.md", "20-security.md", "30-cursorrules.md"])
        text = rendered_pack_text(pack)
        order = ["# General", "Never log secrets", "Answer in British English."]
        self.assertEqual([text.index(s) for s in order], sorted(text.index(s) for s in order))
        self.assertNotIn("alwaysApply", text)  # Cursor's frontmatter stays behind
        self.assertNotIn("Python conventions", text)  # scoped rules are skills, not always loaded

    def test_glob_rules_become_skills_with_a_domains_row(self):
        pack = self.import_fixture()
        meta = tomllib.loads((pack / "pack.toml").read_text())
        self.assertEqual(meta["extensions"]["gatework"]["domains"], [
            {"files": "`*.py`, `scripts/**/*.py`", "skills": ["team-python"]},
            {"files": "`src/**/*.tsx`, `src/**/*.jsx`", "skills": ["team-frontend-react"]}])
        skill = frontmatter(pack / "skills/team-python/SKILL.md")
        self.assertEqual(skill["description"], "Python conventions. Use when working on `*.py`, `scripts/**/*.py`.")
        body = (pack / "skills/team-python/SKILL.md").read_text()
        self.assertIn("10-python.mdc, lines 6-7 -->", body)
        self.assertIn("- Type-annotate public functions.\n- Use `pathlib`, not `os.path`.\n", body)

    def test_described_and_manual_rules_become_skills(self):
        pack = self.import_fixture()
        self.assertEqual(sorted(p.name for p in (pack / "skills").iterdir()),
                         ["team-frontend-react", "team-manual", "team-python", "team-release"])
        release = frontmatter(pack / "skills/team-release/SKILL.md")
        self.assertEqual(release["description"], "Steps to cut a release; use when asked to release")
        code, out = self.run_import(str(FIXTURES / "cursor/.cursor/rules/40-manual.mdc"), "--to", "one")
        self.assertIn("has no description, globs or alwaysApply, so it becomes a skill the model loads only when asked", out)

    def test_the_domains_rows_render_into_gateworks_extensions(self):
        code, out = self.run_import(str(FIXTURES / "cursor"), "--name", "team", "--enable")
        self.assertEqual(code, 0, out)
        from brainrc.validate import extension_warnings, validators
        srcs = sources()
        self.assertEqual([w for w in extension_warnings(srcs, validators(srcs)) if "team" in w], [])

    def test_same_named_skills_from_two_sources_keep_their_domains_rows(self):
        (self.tmp / "a/.cursor/rules").mkdir(parents=True)
        (self.tmp / "b/.cursor/rules").mkdir(parents=True)
        for d in ("a", "b"):
            (self.tmp / d / ".cursor/rules/go.mdc").write_text(f"---\nglobs: {d}/**/*.go\n---\nGo in {d}.\n")
        code, out = self.run_import("a", "b", "--to", "team", "--name", "team")
        self.assertEqual(code, 0, out)
        domains = tomllib.loads((self.tmp / "team/pack.toml").read_text())["extensions"]["gatework"]["domains"]
        self.assertEqual([d["skills"] for d in domains], [["team-go"], ["team-go-2"]])
        self.assertIn("Go in b.", (self.tmp / "team/skills/team-go-2/SKILL.md").read_text())

    def test_globs(self):
        self.assertEqual(globs("*.py, scripts/**/*.py"), ["*.py", "scripts/**/*.py"])
        self.assertEqual(globs('["src/*.ts", \'lib/*.ts\']'), ["src/*.ts", "lib/*.ts"])
        self.assertEqual(globs('"**/*.ts,**/*.tsx"'), ["**/*.ts", "**/*.tsx"])
        self.assertEqual(globs('"*.py, *.pyi"'), ["*.py", "*.pyi"])
        self.assertEqual(globs("src/**/*.{ts,tsx}, *.md"), ["src/**/*.{ts,tsx}", "*.md"])
        self.assertEqual(globs(""), [])

    def test_two_rules_with_one_name_in_one_folder_keep_their_own_rows(self):
        rules = self.tmp / ".cursor/rules"
        rules.mkdir(parents=True)
        (rules / "10-python.mdc").write_text("---\nglobs: a/**\n---\nA.\n")
        (rules / "20-python.mdc").write_text("---\nglobs: b/**\n---\nB.\n")
        p = plan(resolve([".cursor/rules"]), "team")
        self.assertEqual([(d["files"], d["skills"]) for d in p.spec.domains],
                         [("`a/**`", ["team-python"]), ("`b/**`", ["team-python-2"])])
        self.assertIn("B.", p.files["skills/team-python-2/SKILL.md"])

    def test_yaml_frontmatter_forms(self):
        rules = self.tmp / ".cursor/rules"
        rules.mkdir(parents=True)
        (rules / "a.mdc").write_text("\ufeff---\nalwaysApply: \"true\"\n---\nAlways.\n")
        (rules / "b.mdc").write_text("---\ndescription: >\n  Folded\n  text.\nglobs:\n  - \"src/**\"\n---\nB.\n")
        (rules / "10-web").mkdir()
        (rules / "10-web/20-ui.mdc").write_text("---\nglobs: ui/**\n---\nUI.\n")
        p = plan(resolve([".cursor/rules"]), "team")
        self.assertEqual([r.text for r in p.spec.rules], ["Always."])
        self.assertEqual([(s.slug, s.description) for s in p.spec.skills],
                         [("web-ui", "Use when working on `ui/**`."),
                          ("b", "Folded text. Use when working on `src/**`.")])

    def test_an_empty_cursorrules_warns(self):
        (self.tmp / "p").mkdir()
        (self.tmp / "p/.cursorrules").write_text("\n  \n")
        (self.tmp / "p/AGENTS.md").write_text("Hi.\n")
        p = plan(resolve(["p"]), "team")
        self.assertTrue(any(".cursorrules: no text to import" in w for w in p.warnings), p.warnings)

    def test_unclosed_frontmatter_is_body(self):
        (self.tmp / "x.mdc").write_text("---\nalwaysApply: true\nNo closing line.\n")
        code, out = self.run_import("x.mdc", "--to", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("alwaysApply: true", (self.tmp / "team/skills/imported-x/SKILL.md").read_text())

    def test_discover_finds_both_cursor_sources(self):
        self.assertEqual([(f, p.name) for f, p in discover(FIXTURES / "cursor")],
                         [("cursor", "rules"), ("cursor", ".cursorrules")])


class CopilotImportTest(ImportCase):
    """#165: `.github/copilot-instructions.md` and `.github/instructions/*.instructions.md`."""

    def test_copilot_instructions_import_into_a_pack_that_renders_the_same_text(self):
        source = FIXTURES / "copilot/.github/copilot-instructions.md"
        code, out = self.run_import(str(source), "--to", "team", "--name", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("OK:", out)
        self.assertEqual(sorted(p.name for p in (self.tmp / "team/rules").iterdir()),
                         ["10-copilot.md", "20-build.md", "30-style.md", "40-pull-requests.md"])
        self.assertEqual(rendered_pack_text(self.tmp / "team").strip(), normalized(source.read_text()))
        first = (self.tmp / "team/rules/10-copilot.md").read_text()
        self.assertTrue(first.startswith(f"<!-- imported by brainrc from {brainrc.config.tilde(source)}, lines 1-1 -->"))

    def test_a_repo_imports_both_kinds_in_order(self):
        code, out = self.run_import(str(FIXTURES / "copilot"), "--to", "team", "--name", "team")
        self.assertEqual(code, 0, out)
        self.assertNotIn("ERROR", out)
        pack = self.tmp / "team"
        self.assertEqual(sorted(p.name for p in (pack / "rules").iterdir()),
                         ["10-copilot.md", "20-build.md", "30-style.md", "40-pull-requests.md", "50-everywhere.md"])
        self.assertEqual(sorted(p.name for p in (pack / "skills").iterdir()),
                         ["team-backend-go", "team-review", "team-typescript"])
        domains = tomllib.loads((pack / "pack.toml").read_text())["extensions"]["gatework"]["domains"]
        self.assertEqual(domains, [{"files": "`api/**/*.go`", "skills": ["team-backend-go"]},
                                   {"files": "`**/*.ts`, `**/*.tsx`", "skills": ["team-typescript"]}])
        ts = frontmatter(pack / "skills/team-typescript/SKILL.md")
        self.assertEqual(ts["description"], "TypeScript conventions. Use when working on `**/*.ts`, `**/*.tsx`.")
        review = frontmatter(pack / "skills/team-review/SKILL.md")
        self.assertEqual(review["description"], "Code review checklist; use when reviewing a PR")
        self.assertNotIn("applyTo", rendered_pack_text(pack))

    def test_apply_to_globs(self):
        inst = self.tmp / ".github/instructions"
        inst.mkdir(parents=True)
        (inst / "root.instructions.md").write_text('---\napplyTo: "*"\n---\nRoot files.\n')
        (inst / "mixed.instructions.md").write_text('---\napplyTo: "**, docs/**"\n---\nAll files.\n')
        (inst / "review.instructions.md").write_text('---\napplyTo: "**"\nexcludeAgent: "coding-agent"\n---\nCheck.\n')
        p = plan(resolve([".github/instructions"]), "team")
        self.assertEqual([r.slug for r in p.spec.rules], ["mixed"])
        self.assertEqual([s.slug for s in p.spec.skills], ["root"])
        self.assertTrue(any("only for Copilot code review" in w for w in p.warnings), p.warnings)

    def test_format_copilot_reads_any_other_file_as_repo_wide_instructions(self):
        (self.tmp / "team-guidelines-for-ai.md").write_text("## One\n\nA.\n\n## Two\n\nB.\n")
        p = plan(resolve(["team-guidelines-for-ai.md"], "copilot"), "team")
        self.assertEqual([r.slug for r in p.spec.rules], ["one", "two"])
        self.assertEqual(p.spec.skills, [])

    def test_discover_finds_both_copilot_sources(self):
        self.assertEqual([(f, p.name) for f, p in discover(FIXTURES / "copilot")],
                         [("copilot", "copilot-instructions.md"), ("copilot", "instructions")])

    def test_every_format_together(self):
        paths = [str(FIXTURES / d) for d in ("instructions", "cursor", "copilot")]
        code, out = self.run_import(*paths, "--to", "team", "--name", "team")
        self.assertEqual(code, 0, out)
        self.assertIn("OK:", out)
        rules = sorted(p.name for p in (self.tmp / "team/rules").iterdir())
        self.assertEqual(rules[0], "01-team-conventions.md")  # CLAUDE.md's first lines and the AGENTS.md it inlines
        self.assertEqual(rules[-1], "13-everywhere.md")


class SetPackPathTest(unittest.TestCase):
    def test_new_table(self):
        self.assertEqual(set_pack_path("", "team", "~/p"), '[team]\npath = "~/p"\n')
        self.assertEqual(set_pack_path("# mine\n", "team", "~/p"), '# mine\n\n[team]\npath = "~/p"\n')

    def test_replaces_the_tables_origin_turns_it_on_and_keeps_the_rest(self):
        text = '[team]\ngit = "https://x"\nref = "v1"\nenabled = false\nwhy = "x"\n\n[other]\npath = "~/o"\n'
        after = set_pack_path(text, "team", "~/p")
        self.assertEqual(tomllib.loads(after), {"team": {"path": "~/p", "why": "x"},
                                                "other": {"path": "~/o"}})

    def test_a_quoted_table_name_matches(self):
        after = set_pack_path('["team"]\npath = "~/old"\n', "team", "~/p")
        self.assertEqual(tomllib.loads(after), {"team": {"path": "~/p"}})


class ConfigPathTest(unittest.TestCase):
    def test_under_home_is_tilde_else_absolute(self):
        self.assertEqual(brainrc.config.config_path(Path.home() / "x/y"), "~/x/y")
        self.assertEqual(brainrc.config.config_path(Path("/srv/packs/team")), "/srv/packs/team")


if __name__ == "__main__":
    unittest.main()
