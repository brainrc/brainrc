"""`brainrc new skill|agent|rule|command` (E8, #159 to #162): an item that validates, inside a pack."""
import contextlib
import io
import os
import sys
import tomllib
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import brainrc, quiet  # noqa: E402
from test_new_pack import NewPackCase  # noqa: E402

from brainrc import newitem  # noqa: E402
from brainrc.sources import frontmatter, load_pack, render_instructions, Source  # noqa: E402


class NewItemCase(NewPackCase):
    def setUp(self):
        super().setUp()
        code, out = self.new("acme")
        self.assertEqual(code, 0, out)
        self.pack = self.tmp / "acme"
        os.chdir(self.pack)

    def item(self, *args: str) -> tuple[int, str]:
        return quiet(brainrc.cli.main, ["brainrc", "new", *args])

    def ok(self, *args: str) -> str:
        """Run it; it must write the item and validate with no warning (each issue's Done when)."""
        code, out = self.item(*args)
        self.assertEqual(code, 0, out)
        self.assertIn("OK:", out)
        self.assertNotIn("WARN", out)
        self.assertNotIn("ERROR", out)
        code, again = self.validate(str(self.pack))
        self.assertEqual(code, 0, again)
        self.assertNotIn("WARN", again)
        return out


class NewSkillTest(NewItemCase):
    """#159"""

    def test_a_skill_gets_the_prefix_and_its_frontmatter(self):
        self.ok("skill", "deploy", "--description", "Deploy acme services. Use when asked to ship one.")
        skill = self.pack / "skills/acme-deploy/SKILL.md"
        meta = frontmatter(skill)
        self.assertEqual(meta["name"], "acme-deploy")
        self.assertEqual(meta["description"], "Deploy acme services. Use when asked to ship one.")

    def test_a_name_that_has_the_prefix_keeps_it_once(self):
        self.ok("skill", "acme-deploy", "--description", "Deploy acme services.")
        self.assertTrue((self.pack / "skills/acme-deploy/SKILL.md").is_file())
        self.assertFalse((self.pack / "skills/acme-acme-deploy").exists())

    def test_a_domain_skill_has_the_four_sections_and_a_domains_row(self):
        before = (self.pack / "pack.toml").read_text(encoding="utf-8")
        self.ok("skill", "protobuf", "--domain", "*.proto,buf.yaml,src/*.{ts,tsx}")
        text = (self.pack / "skills/acme-protobuf/SKILL.md").read_text(encoding="utf-8")
        heads = ["## Validate (offline)", "## Conventions", "## Review checklist", "## Never without approval"]
        self.assertEqual([text.index(h) for h in heads], sorted(text.index(h) for h in heads))
        self.assertIn("`src/*.{ts,tsx}`", frontmatter(self.pack / "skills/acme-protobuf/SKILL.md")["description"])
        after = (self.pack / "pack.toml").read_text(encoding="utf-8")
        self.assertTrue(after.startswith(before.rstrip("\n")))  # comments and keys kept as written
        rows = tomllib.loads(after)["extensions"]["gatework"]["domains"]
        self.assertEqual(rows, [{"files": "`*.proto`, `buf.yaml`, `src/*.{ts,tsx}`", "skills": ["acme-protobuf"]}])

    def test_the_domains_row_is_added_once(self):
        self.ok("skill", "protobuf", "--domain", "*.proto")
        self.ok("skill", "protobuf", "--domain", "*.proto", "--force")
        self.assertEqual(len(tomllib.loads((self.pack / "pack.toml").read_text(encoding="utf-8"))["extensions"]["gatework"]["domains"]), 1)

    def test_a_pack_toml_that_cant_take_a_row_is_an_error_not_a_crash(self):
        path = self.pack / "pack.toml"
        good = path.read_text(encoding="utf-8")
        for text, says in ((good + '\n[extensions.gatework]\ndomains = [{files = "`*.go`", skills = ["acme-go"]}]\n',
                            "write them as [[extensions.gatework.domains]] tables"),
                           (good + "\nbroken = \n", "pack.toml:")):
            with self.subTest(says):
                path.write_text(text)
                for extra in ([], ["--dry-run"]):
                    code, out = self.item("skill", "protobuf", "--domain", "*.proto", *extra)
                    self.assertEqual(code, 1, out)
                    self.assertIn("ERROR", out)
                    self.assertIn(says, out)
                self.assertFalse((self.pack / "skills/acme-protobuf").exists())
                self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_a_plain_skill_needs_a_description_when_nothing_can_ask(self):
        code, out = self.item("skill", "deploy")
        self.assertEqual(code, 1)
        self.assertIn("--description", out)
        self.assertFalse((self.pack / "skills/acme-deploy").exists())

    def test_it_asks_in_a_terminal(self):
        with mock.patch("sys.stdin.isatty", return_value=True), \
                mock.patch("builtins.input", side_effect=["deploy", "Deploy acme services."]):
            code, out = self.item("skill")
        self.assertEqual(code, 0, out)
        self.assertEqual(frontmatter(self.pack / "skills/acme-deploy/SKILL.md")["description"], "Deploy acme services.")


class NewAgentTest(NewItemCase):
    """#160"""

    def test_an_agent_gets_least_privilege_tools_and_the_handoff_format(self):
        self.ok("agent", "reviewer", "--description", "Reviews acme diffs. Use for a second look at a change.")
        agent = self.pack / "agents/acme-reviewer.md"
        meta = frontmatter(agent)
        self.assertEqual((meta["name"], meta["tools"], meta["model"]), ("acme-reviewer", "Read, Grep, Glob", "inherit"))
        text = agent.read_text(encoding="utf-8")
        self.assertIn("## Handoff", text)
        for part in ("## acme-reviewer · <task> ·", "**Did:**", "**Evidence:**", "**Changed files:**",
                     "**Open issues:**", "**Next:**"):
            self.assertIn(part, text)

    def test_tools_and_model_are_checked_before_writing(self):
        self.ok("agent", "fixer", "--description", "Fixes lint.", "--tools", "Read,Edit,Bash", "--model", "sonnet")
        self.assertEqual(frontmatter(self.pack / "agents/acme-fixer.md")["tools"], "Read, Edit, Bash")
        for args in (["--tools", "Read,Teleport"], ["--model", "gpt"]):
            with self.subTest(args):
                code, out = self.item("agent", "other", "--description", "x", *args)
                self.assertEqual(code, 1, out)
                self.assertFalse((self.pack / "agents/acme-other.md").exists())


class NewRuleTest(NewItemCase):
    """#161"""

    def test_a_rule_takes_the_next_free_number_and_reports_its_cost(self):
        out = self.ok("rule", "testing")
        rule = self.pack / "rules/20-testing.md"
        self.assertEqual(frontmatter(rule), {"trigger": "always_on", "alwaysApply": "true"})
        self.assertRegex(out, r"The rule adds ~\d+ tokens to every session; the pack now loads ~\d+ of its 800\.")
        self.ok("rule", "review")
        self.assertTrue((self.pack / "rules/30-review.md").is_file())
        text = render_instructions([Source("core", brainrc.config.REPO), load_pack(self.pack)])
        self.assertNotIn("trigger: always_on\nalwaysApply: true\n---\n\n# Testing", text)  # brainrc strips it
        self.assertLess(text.index("# Testing"), text.index("# Review"))

    def test_numbering(self):
        def nn(*names):
            rules = self.pack / "rules"
            for p in rules.iterdir():
                p.unlink()
            for name in names:
                (rules / name).write_text("# x\n")
            return newitem.next_rule_number(load_pack(self.pack))
        self.assertEqual(nn(), "10")
        self.assertEqual(nn("10-a.md", "15-b.md"), "20")
        self.assertEqual(nn("01-a.md", "12-b.md"), "20")
        self.assertEqual(nn("90-a.md"), "91")
        self.assertEqual(nn("010-a.md", "120-b.md"), "130")
        with self.assertRaisesRegex(brainrc.config.ConfigError, "renumber"):
            nn("99-a.md")

    def test_a_rule_of_that_name_is_refused(self):
        self.ok("rule", "testing")
        code, out = self.item("rule", "testing")
        self.assertEqual(code, 1)
        self.assertIn("rules/20-testing.md already exists", out)

    def test_over_budget_says_so(self):
        path = self.pack / "pack.toml"
        path.write_text(path.read_text(encoding="utf-8").replace("max_always_tokens = 800", "max_always_tokens = 40"))
        code, out = self.item("rule", "testing")
        self.assertEqual(code, 1)  # validate fails on the budget
        self.assertIn("Over budget", out)


class NewCommandTest(NewItemCase):
    """#162"""

    def test_a_command_gets_its_description_and_arguments(self):
        out = self.ok("command", "release", "--description", "Cut an acme release", "--as-command")
        self.assertNotIn("NOTE", out)
        command = self.pack / "commands/acme-release.md"
        self.assertEqual(frontmatter(command), {"description": "Cut an acme release"})
        self.assertIn("$ARGUMENTS", command.read_text(encoding="utf-8"))

    def test_codex_gets_a_note_and_the_skill_form_on_request(self):
        with mock.patch.object(newitem, "codex_targeted", return_value=True):
            out = self.ok("command", "release", "--description", "Cut an acme release")
            self.assertIn("NOTE Codex skips commands", out)
            self.ok("command", "ship", "--description", "Ship it", "--as-skill", "--argument-hint", "<version>")
        meta = frontmatter(self.pack / "skills/acme-ship/SKILL.md")
        self.assertEqual((meta["name"], meta["disable-model-invocation"], meta["argument-hint"]),
                         ("acme-ship", "true", "<version>"))
        self.assertIn("$ARGUMENTS", (self.pack / "skills/acme-ship/SKILL.md").read_text(encoding="utf-8"))

    def test_only_an_installed_codex_counts(self):
        def harnesses(include_missing=False, **_):
            return {"codex": {}} if include_missing else {"claude": {}}  # enabled, but not installed
        with mock.patch.object(newitem, "load_harnesses", side_effect=harnesses):
            self.assertFalse(newitem.codex_targeted())

    def test_in_a_terminal_codex_is_offered_the_skill_form(self):
        with mock.patch.object(newitem, "codex_targeted", return_value=True), \
                mock.patch("sys.stdin.isatty", return_value=True), mock.patch("builtins.input", return_value=""):
            code, out = self.item("command", "ship", "--description", "Ship it")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.pack / "skills/acme-ship/SKILL.md").is_file())
        self.assertFalse((self.pack / "commands").exists())


class FindPackTest(NewItemCase):
    def test_it_finds_the_pack_from_a_folder_inside_it(self):
        os.chdir(self.pack / "skills")
        self.ok("skill", "deploy", "--description", "Deploy.")
        self.assertTrue((self.pack / "skills/acme-deploy/SKILL.md").is_file())

    def test_outside_a_pack_it_says_how_to_name_one(self):
        os.chdir(self.tmp)
        code, out = self.item("skill", "deploy", "--description", "Deploy.")
        self.assertEqual(code, 1)
        self.assertIn("--pack DIR", out)
        self.ok("skill", "deploy", "--description", "Deploy.", "--pack", "acme")

    def test_options_for_another_kind_are_refused(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = self.item("skill", "deploy", "--description", "Deploy.", "--argument-hint", "x")
        self.assertEqual(code, 2)  # argparse: the skill parser has no such option
        code, out = quiet(lambda: newitem.cmd_new_item("skill", "deploy", description="Deploy.", argument_hint="x"))
        self.assertEqual(code, 1)
        self.assertIn("are for a command", out)

    def test_dry_run_writes_nothing(self):
        before = sorted(p.relative_to(self.pack) for p in self.pack.rglob("*"))
        code, out = self.item("skill", "protobuf", "--domain", "*.proto", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("would write skills/acme-protobuf/SKILL.md", out)
        self.assertIn("would change pack.toml", out)
        self.assertEqual(sorted(p.relative_to(self.pack) for p in self.pack.rglob("*")), before)

    def test_a_link_in_the_way_is_not_written_through(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.pack / "agents").symlink_to(outside, target_is_directory=True)
        code, out = self.item("agent", "x", "--description", "x")
        self.assertEqual(code, 1)
        self.assertIn("is a link", out)
        self.assertEqual(list(outside.iterdir()), [])
