"""Profiles and excludes (#173): what one machine installs, in brainrc.local.toml."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, install_harnesses, quiet  # noqa: E402
from support import home_env, restore_home, rmtree, saved_home

SERVERS = '[servers.docs]\ncommand = "docs-mcp"\nharnesses = ["claude"]\n'


class ProfileCase(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        super().tearDown()

    def local(self, text: str) -> None:
        (self.repo / "brainrc.local.toml").write_text(text)

    def links(self, sub: str) -> list[str]:
        d = self.home / sub
        return sorted(p.name for p in d.iterdir()) if d.is_dir() else []

    def hook_commands(self) -> list[str]:
        path = self.home / ".claude/settings.json"
        settings = json.loads(path.read_text()) if path.is_file() else {}
        return [h["command"] for groups in settings.get("hooks", {}).values() for g in groups for h in g["hooks"]]


class MinimalProfileTest(ProfileCase):
    """Done when: the minimal profile installs rules only."""

    def test_minimal_installs_rules_only(self):
        self.local('profile = "minimal"\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        for sub in (".claude/skills", ".claude/agents", ".codex/skills", ".cursor/skills"):
            self.assertEqual(self.links(sub), [], sub)
        self.assertFalse(os.path.lexists(self.home / ".claude/hooks/brainrc"))
        self.assertEqual(self.hook_commands(), [])
        self.assertEqual(brainrc.link_target(self.home / ".claude/CLAUDE.md"), self.settings_home / "instructions.md")
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual((code, out.strip()), (0, "Everything in sync."))
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_switching_to_minimal_removes_what_full_installed(self):
        quiet(brainrc.cmd_sync, True)
        self.assertIn("brainrc-gatework", self.links(".claude/skills"))
        self.assertTrue(self.hook_commands())
        self.local('profile = "minimal"\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.links(".claude/skills"), [])
        self.assertEqual(self.links(".claude/agents"), [])
        self.assertFalse(os.path.lexists(self.home / ".claude/hooks/brainrc"))
        self.assertEqual(self.hook_commands(), [])

    def test_recommended_installs_items_and_hooks_but_no_mcp_servers(self):
        (self.repo / "mcp").mkdir(exist_ok=True)
        (self.repo / "mcp/servers.toml").write_text(SERVERS)
        quiet(brainrc.cmd_sync, True)
        self.assertIn("docs", (self.home / ".claude.json").read_text())
        self.local('profile = "recommended"\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn("brainrc-gatework", self.links(".claude/skills"))
        self.assertTrue(self.hook_commands())
        self.assertNotIn("docs-mcp", (self.home / ".claude.json").read_text())


class ExcludeTest(ProfileCase):
    def test_exclude_drops_matching_items_and_prunes_their_links(self):
        quiet(brainrc.cmd_sync, True)
        self.assertIn("brainrc-aws", self.links(".claude/skills"))
        self.local('exclude = ["skills/brainrc-aws", "gatework:agents/brainrc-infra-*"]\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("brainrc-aws", self.links(".claude/skills"))
        self.assertNotIn("brainrc-infra-reviewer.md", self.links(".claude/agents"))
        self.assertIn("brainrc-terraform", self.links(".claude/skills"))
        self.assertIn("brainrc-verifier.md", self.links(".claude/agents"))
        self.assertEqual(quiet(brainrc.cmd_sync, False)[1].strip(), "Everything in sync.")

    def test_validate_still_checks_excluded_items(self):
        self.local('profile = "minimal"\nexclude = ["skills/*"]\n')
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        # every skill of the default pack (tests/fixtures/default-pack), though all are excluded
        self.assertIn("8 skills", out)


class ProfileConfigTest(ProfileCase):
    def test_an_unknown_profile_stops_with_its_line(self):
        self.local('# mine\nprofile = "tiny"\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("brainrc.local.toml:2: `profile` must be one of minimal, recommended, full", out)

    def test_exclude_must_be_a_list_of_strings(self):
        self.local('exclude = "skills/brainrc-aws"\n')
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("`exclude` must be a list", out)

    def test_an_unknown_key_warns(self):
        self.local('profiles = "minimal"\n')
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertIn("unknown key `profiles`", out)

    def test_init_writes_the_profile_and_keeps_other_lines(self):
        self.local('# my laptop\nexclude = ["skills/brainrc-aws"]\n')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = brainrc.cli.main(["brainrc", "init", "--yes", "--no-adopt", "--profile", "minimal"])
        self.assertEqual(code, 0, out.getvalue())
        text = (self.repo / "brainrc.local.toml").read_text()
        self.assertEqual(text, 'profile = "minimal"\n# my laptop\nexclude = ["skills/brainrc-aws"]\n')
        self.assertEqual(brainrc.config.install_profile(), ("minimal", ["skills/brainrc-aws"]))

    def test_init_asks_about_the_default_pack(self):
        feed = io.StringIO("\n" * 10 + "n\n")
        answers = iter([True] * 10)

        def ask(question, default=True):
            return False if "gatework" in question else next(answers)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch("sys.stdin", feed), \
                mock.patch.object(brainrc.init, "_ask", ask), mock.patch("sys.stdin.isatty", return_value=True):
            code = brainrc.init.cmd_init(adopt=False)
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("enabled = false", (self.repo / "packs.local.toml").read_text())
        quiet(brainrc.cmd_sync, True)
        self.assertNotIn("brainrc-gatework", self.links(".claude/skills"))
