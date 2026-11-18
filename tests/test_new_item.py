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
        before = (self.pack / "pack.toml").read_text()
        self.ok("skill", "protobuf", "--domain", "*.proto,buf.yaml,src/*.{ts,tsx}")
        text = (self.pack / "skills/acme-protobuf/SKILL.md").read_text()
        heads = ["## Validate (offline)", "## Conventions", "## Review checklist", "## Never without approval"]
        self.assertEqual([text.index(h) for h in heads], sorted(text.index(h) for h in heads))
        self.assertIn("`src/*.{ts,tsx}`", frontmatter(self.pack / "skills/acme-protobuf/SKILL.md")["description"])
        after = (self.pack / "pack.toml").read_text()
        self.assertTrue(after.startswith(before.rstrip("\n")))  # comments and keys kept as written
        rows = tomllib.loads(after)["extensions"]["gatework"]["domains"]
        self.assertEqual(rows, [{"files": "`*.proto`, `buf.yaml`, `src/*.{ts,tsx}`", "skills": ["acme-protobuf"]}])

    def test_the_domains_row_is_added_once(self):
        self.ok("skill", "protobuf", "--domain", "*.proto")
        self.ok("skill", "protobuf", "--domain", "*.proto", "--force")
        self.assertEqual(len(tomllib.loads((self.pack / "pack.toml").read_text())["extensions"]["gatework"]["domains"]), 1)

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
        text = agent.read_text()
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
