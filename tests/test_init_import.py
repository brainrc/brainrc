"""`brainrc init` offers import and a starter profile, and shows counts before writing (#297)."""
import argparse
import contextlib
import io
import os
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import REPO, TempRepoCase, brainrc, quiet  # noqa: E402
from test_init import run  # noqa: E402

from brainrc.init import project_sources  # noqa: E402
from brainrc.sources import render_instructions, sources  # noqa: E402
from brainrc.starter import APP_EXCLUDE, set_exclude, starter_text  # noqa: E402
from support import home_env, restore_home, rmtree, saved_home  # noqa: E402

FIXTURES = REPO / "tests/fixtures/import"


class StarterTextTest(unittest.TestCase):
    def test_each_starter_sets_its_profile_and_excludes(self):
        self.assertEqual(starter_text("", "minimal"), 'profile = "minimal"\n')
        self.assertEqual(starter_text("", "infra"), 'profile = "full"\n')
        app = tomllib.loads(starter_text("", "app"))
        self.assertEqual(app, {"profile": "recommended", "exclude": list(APP_EXCLUDE)})

    def test_switching_starters_keeps_the_users_own_patterns_and_lines(self):
        text = '# laptop\nprofile = "full"\nexclude = ["skills/mine"]\n'
        app = starter_text(text, "app")
        self.assertTrue(app.startswith('# laptop\nprofile = "recommended"\n'))
        self.assertEqual(tomllib.loads(app)["exclude"], ["skills/mine", *APP_EXCLUDE])
        infra = starter_text(app, "infra")
        self.assertEqual(infra, '# laptop\nprofile = "full"\nexclude = ["skills/mine"]\n')

    def test_set_exclude_replaces_a_multi_line_array_and_removes_an_empty_one(self):
        text = 'profile = "full"\nexclude = [\n  "a",  # one\n  "b",\n]\nother = 1\n'
        self.assertEqual(set_exclude(text, ["c"]), 'profile = "full"\nexclude = ["c"]\nother = 1\n')
        self.assertEqual(set_exclude(text, []), 'profile = "full"\nother = 1\n')
        self.assertEqual(set_exclude("", []), "")
        self.assertEqual(set_exclude('[t]\nexclude = ["x"]\n', ["y"]), 'exclude = ["y"]\n[t]\nexclude = ["x"]\n')


class InitImportTest(TempRepoCase):
    """A fresh HOME with Claude Code installed, run from a project folder with instruction files."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        (self.home / ".claude").mkdir()
        self.project = Path(tempfile.mkdtemp()).resolve() / "shop"
        shutil.copytree(FIXTURES / "cursor", self.project)
        (self.project / "AGENTS.md").write_text("## Build\n\nRun `make`.\n\n## Test\n\nRun `make test`.\n")
        self.old_cwd = os.getcwd()
        os.chdir(self.project)

    def tearDown(self):
        os.chdir(self.old_cwd)
        restore_home(self.old_home)
        rmtree(self.home)
        rmtree(self.project.parent)
        super().tearDown()

    @property
    def pack(self) -> Path:
        return self.settings_home / "imported/imported"

    def test_yes_names_the_files_and_imports_nothing(self):
        code, out = run("--yes")
        self.assertEqual(code, 0, out)
        self.assertIn("AGENTS.md", out)
        self.assertIn("init --import", out)
        self.assertFalse(self.pack.exists())
        self.assertFalse((self.repo / "packs.local.toml").exists())

    def test_import_writes_a_pack_that_validates_and_apply_loads(self):
        code, out = run("--yes", "--import")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.pack / "pack.toml").is_file())
        packs = tomllib.loads((self.repo / "packs.local.toml").read_text())
        self.assertEqual(brainrc.config.expand(packs["imported"]["path"]), self.pack)
        self.assertIn("Run `make test`.", render_instructions(sources()))
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)

    def test_counts_come_before_anything_is_written(self):
        code, out = run("--yes", "--import", "--starter", "app")
        self.assertEqual(code, 0, out)
        counts = out.index("Before writing:")
        self.assertLess(counts, out.index("Wrote"))
        self.assertRegex(out, r"files: 12 new, 0 changed, 0 moved aside")
        self.assertIn("hooks: 3 after apply (claude 3)", out)
        self.assertRegex(out, r"tokens: ~\d+ loaded in every session \(rules \d+, descriptions \d+\)")

    def test_the_minimal_starter_counts_no_hooks_and_no_descriptions(self):
        code, out = run("--yes", "--starter", "minimal", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("hooks: 0 after apply (the minimal profile installs none)", out)
        self.assertIn("descriptions 0)", out)
        self.assertFalse((self.repo / "brainrc.local.toml").exists())

    def test_the_app_starter_leaves_out_infra_skills_on_apply(self):
        code, out = run("--yes", "--starter", "app")
        self.assertEqual(code, 0, out)
        self.assertIn("starts with the app profile (recommended)", out)
        self.assertEqual(brainrc.config.install_profile(), ("recommended", list(APP_EXCLUDE)))
        quiet(brainrc.cmd_sync, True)
        linked = sorted(p.name for p in (self.home / ".claude/skills").iterdir())
        self.assertIn("brainrc-work", linked)
        self.assertNotIn("brainrc-aws", linked)
        self.assertNotIn("brainrc-terraform", linked)

    def test_interactive_asks_import_and_starter_then_writes_on_yes(self):
        # manage claude; import yes; gatework yes; starter infra; write yes
        code, out = run(stdin="y\ny\ny\ninfra\ny\n", tty=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Which starter profile? [minimal/APP/infra]", out)
        self.assertTrue((self.pack / "pack.toml").is_file())
        self.assertEqual(brainrc.config.install_profile(), ("full", []))

    def test_interactive_no_at_the_end_writes_nothing(self):
        claude_md = self.home / ".claude/CLAUDE.md"
        claude_md.write_text("Mine.\n")
        code, out = run(stdin="n\ny\ny\ny\napp\nn\n", tty=True)  # leave claude unmanaged, then say no
        self.assertEqual(code, 0, out)
        self.assertIn("Nothing written.", out)
        for name in ("harnesses.local.toml", "packs.local.toml", "brainrc.local.toml"):
            self.assertFalse((self.repo / name).exists(), name)
        self.assertFalse(self.pack.exists())
        self.assertEqual(claude_md.read_text(), "Mine.\n")

    def test_interactive_end_of_input_imports_nothing_and_starts_with_app(self):
        code, out = run(stdin="", tty=True)
        self.assertEqual(code, 0, out)
        self.assertFalse(self.pack.exists())
        self.assertEqual(brainrc.config.install_profile()[0], "recommended")

    def test_an_earlier_import_is_left_alone(self):
        self.assertEqual(run("--yes", "--import")[0], 0)
        (self.project / "AGENTS.md").write_text("## Changed\n\nNew text.\n")
        code, out = run("--yes", "--import")
        self.assertEqual(code, 0, out)
        self.assertIn("already has files, so init leaves them", out)
        self.assertNotIn("New text.", render_instructions(sources()))

    def test_no_files_are_offered_from_home_or_a_brainrc_checkout(self):
        self.assertTrue(project_sources(self.project, set()))
        self.assertEqual(project_sources(REPO, set()), [])
        (self.home / "AGENTS.md").write_text("Home.\n")
        self.assertEqual(project_sources(self.home, set()), [])
        skip = {(self.project / "AGENTS.md").resolve()}
        self.assertNotIn("AGENTS.md", [p.name for _, p in project_sources(self.project, skip)])

    def test_profile_and_starter_are_exclusive(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = brainrc.cli.main(["brainrc", "init", "--yes", "--profile", "full", "--starter", "app"])
        self.assertEqual(code, 2)
        self.assertIn("not allowed with argument", err.getvalue())


if __name__ == "__main__":
    unittest.main()
