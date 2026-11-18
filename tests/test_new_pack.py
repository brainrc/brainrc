"""`brainrc new pack` (#150): a new pack that validates on its first run, written by the importers' writer."""
import os
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import REPO, TempRepoCase, brainrc, quiet  # noqa: E402
from test_frozen import FrozenCase  # noqa: E402

from brainrc import lock, newpack  # noqa: E402
from brainrc.newpack import Answers, spec_for  # noqa: E402
from brainrc.scaffold import render_pack  # noqa: E402
from brainrc.sources import load_pack, sources  # noqa: E402
from support import rmtree  # noqa: E402

VERSION = (REPO / "VERSION").read_text().strip()
HOME_PATH = "/ho" + "me/bob/src"  # split so the repo's own no-home-paths hook doesn't flag this file


def files_for(**kw) -> dict[str, str]:
    return render_pack(spec_for(Answers(**{"name": "acme", **kw})))


class RenderTest(unittest.TestCase):
    def test_the_layout(self):
        files = files_for(harnesses=["claude", "codex"])
        self.assertEqual(sorted(files), [
            ".github/workflows/validate.yml", ".gitignore", ".pre-commit-config.yaml", "AGENTS.md",
            "CLAUDE.md", "README.md", "pack.toml", "rules/10-acme.md", "skills/acme-facts/SKILL.md",
            "tests/test_pack.py", "tripwires.toml"])
        for rel, text in files.items():
            self.assertNotIn("{{", text, rel)
        self.assertEqual(files["CLAUDE.md"], "@AGENTS.md\n")

    def test_pack_toml(self):
        meta = tomllib.loads(files_for()["pack.toml"])
        self.assertEqual((meta["name"], meta["prefix"], meta["test"]), ("acme", "acme-", "tests"))
        self.assertEqual(meta["max_always_tokens"], newpack.MAX_ALWAYS_TOKENS)
        major, minor = VERSION.split(".")[:2]
        self.assertEqual(meta["requires_core"], f">={major}.{minor}, <{major}.{int(minor) + 1}")
        self.assertNotIn("extensions", meta)
        self.assertNotIn("id", meta)

    def test_ci_and_pre_commit_pin_this_core(self):
        files = files_for()
        self.assertIn(f"brainrc/brainrc/.github/actions/validate-pack@v{VERSION}\n",
                      files[".github/workflows/validate.yml"])
        self.assertIn(f"rev: v{VERSION}\n", files[".pre-commit-config.yaml"])

    def test_harness_pointers_follow_the_harnesses(self):
        self.assertNotIn("CLAUDE.md", files_for(harnesses=["codex"]))
        self.assertNotIn("GEMINI.md", files_for(harnesses=["claude"]))
        self.assertEqual(files_for(harnesses=["gemini"])["GEMINI.md"], "@AGENTS.md\n")

    def test_tickets(self):
        jira = tomllib.loads(files_for(name="my-team", ticket="jira", host="my-team.atlassian.net")["pack.toml"])
        self.assertEqual(jira["extensions"]["gatework"]["ticket"],
                         {"connector": "brainrc-ticket-jira", "refs": ["MYTEAM-*"], "host": "my-team.atlassian.net"})
        with self.assertRaisesRegex(brainrc.config.ConfigError, "--host"):
            files_for(ticket="jira")
        gh = tomllib.loads(files_for(ticket="github", refs=["gh:*"])["pack.toml"])
        self.assertEqual(gh["extensions"]["gatework"]["ticket"]["connector"], "brainrc-ticket-github")
        self.assertEqual(newpack.default_refs("jira", "42"), ["PROJ-*"])
        self.assertEqual(newpack.default_refs("local", "acme"), ["local:*"])

    def test_an_id_makes_the_owner_the_prefix(self):
        files = files_for(name="tools", pack_id="jdoe/tools")
        meta = tomllib.loads(files["pack.toml"])
        self.assertEqual((meta["id"], meta["prefix"]), ("jdoe/tools", "jdoe-"))
        self.assertIn("skills/jdoe-facts/SKILL.md", files)

    def test_every_naming_rule_is_checked_before_anything_is_written(self):
        for kw in ({"name": "Acme"}, {"name": "a"}, {"prefix": "acme"}, {"name": "brainrc-x"},
                   {"name": "aws-tools"}, {"name": "brainrx"}, {"name": "tools", "pack_id": "jdoe/tools", "prefix": "tools-"}):
            with self.subTest(**kw), self.assertRaises(brainrc.config.ConfigError):
                files_for(**kw)


class NewPackCase(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmp)
        tty = mock.patch("sys.stdin.isatty", return_value=False)
        tty.start()
        self.addCleanup(tty.stop)

    def tearDown(self):
        os.chdir(self.old_cwd)
        rmtree(self.tmp)
        super().tearDown()

    def new(self, *args: str) -> tuple[int, str]:
        return quiet(brainrc.cli.main, ["brainrc", "new", "pack", *args])

    def validate(self, pack: str) -> tuple[int, str]:
        return quiet(brainrc.cli.main, ["brainrc", "validate", "--pack", pack])


class NewPackTest(NewPackCase):
    def test_new_pack_then_validate_is_ok(self):
        code, out = self.new("acme")
        self.assertEqual(code, 0, out)
        self.assertIn("OK:", out)
        self.assertIn("(packs: gatework, acme)", out)
        self.assertIn('[packs.acme]\npath = "acme"', out)  # for this project's brainrc.toml
        code, out = self.validate("acme")
        self.assertEqual(code, 0, out)
        self.assertEqual(load_pack(self.tmp / "acme").name, "acme")

    def test_a_ticket_system_validates_against_gatework(self):
        code, out = self.new("acme", "--ticket", "jira", "--refs", "ACME-*,OPS-*", "--host", "acme.atlassian.net",
                              "--to", "packs/acme")
        self.assertEqual(code, 0, out)
        meta = tomllib.loads((self.tmp / "packs/acme/pack.toml").read_text())
        self.assertEqual(meta["extensions"]["gatework"]["ticket"]["refs"], ["ACME-*", "OPS-*"])

    def test_its_tripwire_and_tests_catch_what_they_are_for(self):
        self.assertEqual(self.new("acme")[0], 0)
        readme = self.tmp / "acme/README.md"
        readme.write_text(readme.read_text() + f"\nClone it to {HOME_PATH}/acme.\n")
        code, out = self.validate("acme")
        self.assertEqual(code, 1, out)
        self.assertIn("tripwire home-folder-path", out)
        readme.write_text(readme.read_text().replace(f"{HOME_PATH}/acme", "~/src/acme"))
        facts = self.tmp / "acme/skills/acme-facts/SKILL.md"
        secret = "api_key = " + "x1y2" * 6
        facts.write_text(facts.read_text() + f"\n{secret}\n")
        code, out = self.validate("acme")
        self.assertEqual(code, 1, out)
        self.assertIn("skills/acme-facts/SKILL.md:", out)
        self.assertIn("looks like a secret", out)
        self.assertNotIn(secret, out)

    def test_a_folder_with_files_is_refused_unless_it_is_an_earlier_pack(self):
        (self.tmp / "acme").mkdir()
        (self.tmp / "acme/notes.md").write_text("mine\n")
        code, out = self.new("acme")
        self.assertEqual(code, 1)
        self.assertIn("already has files", out)
        code, out = self.new("acme", "--force")
        self.assertEqual(code, 1)
        self.assertIn("no pack.toml", out)
        self.assertEqual(self.new("acme", "--to", "other")[0], 0)
        self.assertEqual(self.new("acme", "--to", "other", "--force", "--description", "Second.")[0], 0)
        self.assertIn("Second.", (self.tmp / "other/README.md").read_text())

    def test_dry_run_writes_nothing(self):
        code, out = self.new("acme", "--dry-run", "--enable")
        self.assertEqual(code, 0, out)
        self.assertIn("would write .github/workflows/validate.yml", out)
        self.assertIn("Would add [acme]", out)
        self.assertEqual(list(self.tmp.iterdir()), [])
        self.assertFalse((self.repo / "packs.local.toml").exists())

    def test_enable_adds_it_and_apply_sources_it(self):
        code, out = self.new("acme", "--enable", "--harness", "claude")
        self.assertEqual(code, 0, out)
        packs = tomllib.loads((self.repo / "packs.local.toml").read_text())
        self.assertEqual(brainrc.config.expand(packs["acme"]["path"]), self.tmp / "acme")
        self.assertIn("acme", [s.name for s in sources()])

    def test_bad_input_fails_before_writing(self):
        for args, why in ((("brainrx",), "edits from the official name"), ((), "name the pack"),
                          (("acme", "--harness", "vim"), "no such harness")):
            with self.subTest(args=args):
                code, out = self.new(*args)
                self.assertEqual(code, 1, out)
                self.assertIn(why, out)
        self.assertEqual(list(self.tmp.iterdir()), [])


class AskTest(NewPackCase):
    def answer(self, *lines: str, args: tuple[str, ...] = ()) -> tuple[int, str]:
        with mock.patch("sys.stdin.isatty", return_value=True), \
                mock.patch("builtins.input", side_effect=list(lines)):
            return self.new(*args)

    def test_asks_for_what_is_not_given_and_re_asks_a_bad_name(self):
        code, out = self.answer("Bad Name", "", "acme", "", "claude,gemini", "jira", "", "acme.atlassian.net", "")
        self.assertEqual(code, 0, out)
        self.assertIn("`name` must be ASCII lowercase", out)
        meta = tomllib.loads((self.tmp / "acme/pack.toml").read_text())
        self.assertEqual(meta["extensions"]["gatework"]["ticket"]["refs"], ["ACME-*"])
        self.assertTrue((self.tmp / "acme/GEMINI.md").is_file())

    def test_given_answers_are_not_asked_and_yes_asks_nothing(self):
        code, out = self.answer("ops-", "", "none", args=("acme",))
        self.assertEqual(code, 0, out)
        self.assertEqual(tomllib.loads((self.tmp / "acme/pack.toml").read_text())["prefix"], "ops-")
        code, out = self.answer(args=("other", "--yes"))
        self.assertEqual(code, 0, out)


class ProjectPackTest(FrozenCase):
    """E27: a new pack inside a repo is listed in brainrc.toml, installed and locked like any other."""

    def test_a_new_pack_in_a_project_is_locked_and_checks_clean(self):
        with mock.patch("sys.stdin.isatty", return_value=False):
            code, out = quiet(brainrc.cli.main, ["brainrc", "new", "pack", "acme", "--to", "tools/acme-pack"])
        self.assertEqual(code, 0, out)
        self.manifest('[packs.acme]\npath = "tools/acme-pack"\n')
        self.apply()
        files = lock.read(self.proj / "brainrc.lock")["packs"]["acme"]["files"]
        self.assertIn("skills/acme-facts/SKILL.md", files)
        self.assertIn("rules/10-acme.md", files)
        got, out = quiet(brainrc.cli.cmd_check, None)
        self.assertEqual(got, 0, out)


if __name__ == "__main__":
    unittest.main()
