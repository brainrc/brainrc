"""`brainrc check` (#285): drift between the repo, the packs and brainrc.lock fails, offline."""
import os
import re
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import rmtree  # noqa: E402
from test_brainrc import git, quiet  # noqa: E402
from test_frozen import FrozenCase  # noqa: E402
from test_lock import rev  # noqa: E402
from test_project_scope import make_team_pack  # noqa: E402

import brainrc  # noqa: E402


class CheckCase(FrozenCase):
    def check(self, code: int = 0, scope: str | None = None) -> str:
        with mock.patch("brainrc.packs.subprocess.run", side_effect=AssertionError("no git, no network")):
            got, out = quiet(brainrc.cli.cmd_check, scope)
        self.assertEqual(got, code, out)
        return out


class ProjectCheckTest(CheckCase):
    def setUp(self):
        super().setUp()
        make_team_pack(self.proj / "tools/team-pack")
        self.manifest('[packs.team]\npath = "tools/team-pack"\n')
        self.apply()
        self.lock_text = (self.proj / "brainrc.lock").read_text()

    def test_a_fresh_apply_is_in_sync_and_check_writes_nothing(self):
        before = sorted(p for p in self.proj.rglob("*") if ".git" not in p.parts)
        out = self.check()
        self.assertIn("In sync with brainrc.lock.", out)
        self.assertEqual(sorted(p for p in self.proj.rglob("*") if ".git" not in p.parts), before)

    def test_a_hand_edited_skill_is_named(self):
        skill = self.proj / ".agents/skills/team-deploy/SKILL.md"
        skill.write_text(skill.read_text() + "Edited.\n")
        out = self.check(code=1)
        self.assertIn("DRIFT .agents/skills/team-deploy/SKILL.md: differs from brainrc.lock and isn't "
                      "brainrc's output (`install --frozen` refuses it without --force)", out)
        self.assertIn("1 difference from brainrc.lock.", out)

    def test_brainrc_s_own_output_for_another_lock_is_named_as_such(self):
        skill = self.proj / "tools/team-pack/skills/team-deploy/SKILL.md"
        skill.write_text(skill.read_text() + "Changed.\n")
        self.apply()
        (self.proj / "brainrc.lock").write_text(self.lock_text)  # e.g. the committed lock, pulled back
        out = self.check(code=1)
        self.assertIn(".agents/skills/team-deploy/SKILL.md: differs from brainrc.lock (brainrc wrote it for another lock", out)

    def test_a_missing_or_added_file_is_named(self):
        (self.proj / ".agents/skills/team-deploy/SKILL.md").unlink()
        (self.proj / ".agents/skills/team-context/notes.md").write_text("mine\n")
        out = self.check(code=1)
        self.assertIn(".agents/skills/team-deploy/SKILL.md: missing", out)
        self.assertIn(".agents/skills/team-context/notes.md: not in brainrc.lock", out)

    def test_the_agents_md_block(self):
        agents = self.proj / "AGENTS.md"
        agents.write_text("# Mine\n\n" + agents.read_text())  # text outside the block is yours
        self.check()
        agents.write_text(agents.read_text().replace("- Team rule.", "- Other rule."))
        self.assertIn("DRIFT AGENTS.md: brainrc's block differs", self.check(code=1))
        agents.write_text("# Mine\n")
        self.assertIn("DRIFT AGENTS.md: brainrc's block is missing", self.check(code=1))

    def test_a_changed_pack_without_apply(self):
        rule = self.proj / "tools/team-pack/rules/50-team.md"
        rule.write_text(rule.read_text() + "- New rule.\n")
        out = self.check(code=1)
        self.assertIn("DRIFT pack team: rules/50-team.md differs from brainrc.lock", out)
        self.apply()
        self.check()

    def test_brainrc_toml_changed_without_apply(self):
        self.manifest('[packs.team]\npath = "tools/team-pack"\n\n[packs.gatework]\nenabled = false\n')
        out = self.check(code=1)
        self.assertIn("pack gatework: in brainrc.lock but not enabled in brainrc.toml", out)

    def test_an_exclude_added_without_apply(self):
        self.manifest('exclude = ["skills/team-deploy"]\n\n[packs.team]\npath = "tools/team-pack"\n')
        out = self.check(code=1)
        self.assertIn("pack team: skills/team-deploy/SKILL.md is in brainrc.lock but not in the pack", out)

    def test_a_fresh_checkout_without_the_git_pack_is_checked_through_its_files(self):
        rmtree(self.settings_home / "project-packs")
        out = self.check()
        self.assertIn("NOTE pack gatework: not fetched on this machine", out)
        (self.proj / ".agents/skills/brainrc-work/SKILL.md").write_text("changed\n")
        self.assertIn("DRIFT .agents/skills/brainrc-work/SKILL.md", self.check(code=1))

    def test_harnesses_changed_without_apply_fails_even_without_the_git_pack(self):
        rmtree(self.settings_home / "project-packs")  # CI: nothing fetched
        self.manifest('harnesses = []\n\n[packs.team]\npath = "tools/team-pack"\n')
        out = self.check(code=1)
        self.assertIn("DRIFT .claude/skills/brainrc-work/: in brainrc.lock, but brainrc.toml no longer asks for it", out)
        self.assertIn("DRIFT CLAUDE.md: brainrc's block is in brainrc.lock, but brainrc.toml no longer asks", out)
        self.assertNotIn(".agents/skills/brainrc-work/", out)

    def test_a_moved_tag_is_reported_and_does_not_fail(self):
        a, b = rev(self.bare, "v1"), rev(self.bare, "v2")
        self.move_tag("v1", "v2")
        clone = next((self.settings_home / "project-packs").iterdir())
        git("fetch", "-q", "--depth", "1", self.url, "v1", cwd=clone)  # this machine saw the new tag
        git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=clone)
        out = self.check()
        self.assertIn(f"MOVED     gatework  v1: {a[:12]} -> {b[:12]}", out)
        self.assertIn("In sync with brainrc.lock.", out)

    def test_a_tampered_lock_output_is_caught_when_every_pack_is_here(self):
        lock_file = self.proj / "brainrc.lock"
        text = re.sub(r'(".agents/skills/team-deploy/SKILL.md" = "sha256:)[0-9a-f]{64}', r"\g<1>" + "3" * 64,
                      self.lock_text)
        lock_file.write_text(text)
        out = self.check(code=1)
        self.assertIn(".agents/skills/team-deploy/SKILL.md: the packs at their locked state don't produce", out)
        self.assertIn(".agents/skills/team-deploy/SKILL.md: differs from brainrc.lock", out)

    def test_no_lock(self):
        (self.proj / "brainrc.lock").unlink()
        self.assertIn("no brainrc.lock next to brainrc.toml", self.check(code=1))


class UserCheckTest(CheckCase):
    def test_user_scope(self):
        self.apply()
        out = self.check(scope="user")
        self.assertIn("In sync with brainrc.lock.", out)
        skill = self.settings_home / "packs/gatework/skills/brainrc-work/SKILL.md"
        skill.write_text("edited in the clone\n")
        out = self.check(code=1, scope="user")
        self.assertIn("DRIFT pack gatework: skills/brainrc-work/SKILL.md differs from brainrc.lock", out)

    def test_outside_a_project_it_is_the_user_scope(self):
        self.apply()
        os.chdir(self.proj.parent)
        self.assertIn("User scope", self.check())
        self.check(code=2, scope="project")

    def test_the_command_line(self):
        self.apply()
        code, out = quiet(brainrc.main, ["brainrc", "check", "--scope", "user"])
        self.assertEqual(code, 0, out)
