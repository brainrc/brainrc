"""`install --frozen` (#284): exactly what brainrc.lock records, or fail, name the item and write
nothing. Gatework, a default git pack, is the main case."""
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import home_env, rmtree  # noqa: E402
from test_brainrc import home_files, install_harnesses, quiet  # noqa: E402
from test_lock import GitLockCase, rev  # noqa: E402
from test_project_scope import make_team_pack  # noqa: E402

from brainrc import lock  # noqa: E402
import brainrc  # noqa: E402


def tree(root: Path) -> dict[str, bytes]:
    """Every file under root, links followed, by path: what a harness or a repo reader sees."""
    found = {}
    for dirpath, _, files in os.walk(root, followlinks=True):
        for f in files:
            p = Path(dirpath) / f
            found[p.relative_to(root).as_posix()] = p.read_bytes()
    return found


class FrozenCase(GitLockCase):
    def frozen(self, code: int = 0, scope: str | None = None, force: bool = False) -> str:
        got, out = quiet(brainrc.cli.cmd_install, True, scope, force)
        self.assertEqual(got, code, out)
        return out

    def new_machine(self) -> None:
        """A second machine: a fresh HOME and settings home, the same core checkout."""
        self.home = Path(tempfile.mkdtemp()).resolve()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        self.settings_home = Path(tempfile.mkdtemp()) / "brainrc"
        os.environ["BRAINRC_HOME"] = str(self.settings_home)
        self.addCleanup(rmtree, self.home, True)
        self.addCleanup(rmtree, self.settings_home.parent, True)
        self.user_lock = self.settings_home / "brainrc.lock"

    def edit_lock(self, path: Path, fn) -> None:
        path.write_text(fn(path.read_text()))


class UserFrozenTest(FrozenCase):
    def setUp(self):
        super().setUp()
        self.apply()
        self.text = self.user_lock.read_text()
        self.first = tree(self.home / ".claude")

    def install_elsewhere(self, text: str | None = None, code: int = 0) -> str:
        self.new_machine()
        self.user_lock.parent.mkdir(parents=True)
        self.user_lock.write_text(text or self.text)
        return self.frozen(code)

    def test_two_machines_get_byte_identical_files_and_lock(self):
        self.install_elsewhere()
        self.assertEqual(tree(self.home / ".claude"), self.first)
        self.assertEqual(self.user_lock.read_text(), self.text)
        self.apply()  # and a later apply relocks to the very same lock
        self.assertEqual(self.user_lock.read_text(), self.text)

    def test_a_moved_tag_changes_nothing(self):
        self.move_tag("v1", "v2")
        self.install_elsewhere()
        clone = self.settings_home / "packs/gatework"
        self.assertEqual((clone / ".git/HEAD").read_text().strip(), rev(self.bare, "v2~1"))
        self.assertFalse((self.home / ".claude/skills/brainrc-new").exists())
        self.assertEqual(tree(self.home / ".claude"), self.first)

    def test_a_missing_commit_fails_names_it_and_writes_nothing(self):
        bogus = "0123456789abcdef0123456789abcdef01234567"
        out = self.install_elsewhere(re.sub(r'commit = "[0-9a-f]+"', f'commit = "{bogus}"', self.text), code=1)
        self.assertIn(f"pack gatework: locked commit {bogus[:12]} can't be fetched", out)
        self.assertIn("Nothing written.", out)
        self.assertEqual(home_files(self.home), [])
        self.assertEqual(sorted(p.name for p in (self.settings_home / "packs").iterdir()), [])

    def test_a_differing_file_hash_fails_and_writes_nothing(self):
        text = re.sub(r'("skills/brainrc-work/SKILL.md" = "sha256:)[0-9a-f]{64}', r"\g<1>" + "0" * 64, self.text)
        out = self.install_elsewhere(text, code=1)
        self.assertIn("ERROR pack gatework: skills/brainrc-work/SKILL.md differs from brainrc.lock", out)
        self.assertEqual(home_files(self.home), [])
        self.assertFalse((self.settings_home / "packs/gatework").exists())

    def test_an_extra_or_missing_file_fails(self):
        text = self.text.replace('"pack.toml" = ', '"skills/brainrc-gone/SKILL.md" = "sha256:' + "1" * 64 + '"\n"pack.toml" = ')
        out = self.install_elsewhere(text, code=1)
        self.assertIn("pack gatework: skills/brainrc-gone/SKILL.md is in brainrc.lock but not in the pack", out)

    def test_a_pack_only_in_the_config_or_only_in_the_lock_fails(self):
        out = self.install_elsewhere(self.text.split("\n[packs.gatework]")[0] + "\n", code=1)
        self.assertIn("pack gatework: in packs.toml but not in brainrc.lock", out)
        (self.repo / "packs.local.toml").write_text("[gatework]\nenabled = false\n")
        self.user_lock.write_text(self.text)
        out = self.frozen(code=1)
        self.assertIn("pack gatework: in brainrc.lock but not enabled in packs.toml", out)
        self.assertEqual(home_files(self.home), [])

    def test_another_ref_in_the_config_fails(self):
        (self.repo / "packs.local.toml").write_text('[gatework]\nref = "v2"\n')
        out = self.frozen(code=1)
        self.assertIn("pack gatework: `ref` is 'v2' in packs.toml but 'v1' in brainrc.lock", out)

    def test_no_lock_fails(self):
        self.new_machine()
        out = self.frozen(code=1)
        self.assertIn("no brainrc.lock at", out)

    def test_an_existing_clone_at_the_locked_commit_is_reused_offline(self):
        clone = self.settings_home / "packs/gatework"
        before = clone.stat().st_ino
        rmtree(self.bare)  # no remote at all
        self.frozen()
        self.assertEqual(clone.stat().st_ino, before)


class ProjectFrozenTest(FrozenCase):
    def setUp(self):
        super().setUp()
        make_team_pack(self.proj / "tools/team-pack")
        self.manifest('[packs.team]\npath = "tools/team-pack"\n')
        self.apply()
        self.lock_text = (self.proj / "brainrc.lock").read_text()
        self.first = {k: v for k, v in tree(self.proj).items() if not k.startswith(".git/")}

    def second_checkout(self) -> Path:
        """The same commit of the repo on another machine: brainrc.toml, the lock and the pack, but
        none of the generated files."""
        self.new_machine()
        other = Path(tempfile.mkdtemp()).resolve() / "app"
        self.addCleanup(rmtree, other.parent, True)
        (other / ".git").mkdir(parents=True)
        for rel in ("brainrc.toml", "brainrc.lock"):
            shutil.copy(self.proj / rel, other / rel)
        shutil.copytree(self.proj / "tools", other / "tools")
        os.chdir(other)
        return other

    def test_two_machines_write_byte_identical_project_files(self):
        other = self.second_checkout()
        out = self.frozen()
        self.assertIn("CREATE    project   .agents/skills/brainrc-work/", out)
        self.assertIn("Project installed from brainrc.lock.", out)
        self.assertEqual({k: v for k, v in tree(other).items() if not k.startswith(".git/")}, self.first)
        self.assertEqual((other / "brainrc.lock").read_text(), self.lock_text)
        self.assertEqual(home_files(self.home), [])  # the project's lock installs nothing for the user

    def test_a_moved_tag_changes_nothing_in_the_project(self):
        self.move_tag("v1", "v2")
        other = self.second_checkout()
        self.frozen()
        self.assertFalse((other / ".agents/skills/brainrc-new").exists())
        self.assertEqual({k: v for k, v in tree(other).items() if not k.startswith(".git/")}, self.first)

    def test_a_tampered_output_hash_fails_and_writes_nothing(self):
        other = self.second_checkout()
        self.edit_lock(other / "brainrc.lock", lambda t: re.sub(
            r'(".agents/skills/team-deploy/SKILL.md" = "sha256:)[0-9a-f]{64}', r"\g<1>" + "2" * 64, t))
        out = self.frozen(code=1)
        self.assertIn(".agents/skills/team-deploy/SKILL.md: the packs at their locked state don't produce", out)
        self.assertFalse((other / ".agents").exists())
        self.assertFalse((other / "AGENTS.md").exists())

    def test_a_pack_added_to_brainrc_toml_but_not_locked_fails(self):
        other = self.second_checkout()
        (other / "brainrc.toml").write_text((other / "brainrc.toml").read_text() + '\n[packs.more]\npath = "tools/team-pack"\n')
        out = self.frozen(code=1)
        self.assertIn("pack more: in brainrc.toml but not in brainrc.lock (run apply to relock)", out)
        self.assertFalse((other / ".agents").exists())

    def test_a_changed_path_pack_fails(self):
        other = self.second_checkout()
        rule = other / "tools/team-pack/rules/50-team.md"
        rule.write_text(rule.read_text() + "- Unreviewed rule.\n")
        out = self.frozen(code=1)
        self.assertIn("pack team: rules/50-team.md differs from brainrc.lock", out)

    def test_the_user_scope_can_be_asked_for_in_a_project(self):
        out = self.frozen(scope="user")
        self.assertNotIn("Project", out)

    def test_a_file_brainrc_did_not_write_fails_unless_forced(self):
        other = self.second_checkout()
        mine = other / ".agents/skills/team-deploy/SKILL.md"
        mine.parent.mkdir(parents=True)
        mine.write_text("my own skill\n")
        out = self.frozen(code=1)
        self.assertIn("ERROR .agents/skills/team-deploy/SKILL.md: brainrc didn't write this file", out)
        self.assertIn("pass --force to overwrite them", out)
        self.assertEqual(mine.read_text(), "my own skill\n")
        self.assertFalse((other / ".agents/skills/team-context").exists())  # nothing written
        self.frozen(force=True)
        self.assertEqual({k: v for k, v in tree(other).items() if not k.startswith(".git/")}, self.first)

    def test_a_hand_edited_block_fails_unless_forced(self):
        other = self.second_checkout()
        self.frozen()
        agents = other / "AGENTS.md"
        agents.write_text(agents.read_text().replace("- Team rule.", "- My rule."))
        out = self.frozen(code=1)
        self.assertIn("AGENTS.md: brainrc's block was edited by hand", out)
        self.assertIn("- My rule.", agents.read_text())
        self.frozen(force=True)
        self.assertIn("- Team rule.", agents.read_text())

    def test_a_block_with_only_windows_line_endings_is_not_a_hand_edit(self):
        other = self.second_checkout()
        self.frozen()
        agents = other / "AGENTS.md"
        agents.write_bytes(agents.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        self.frozen()
        self.assertEqual(agents.read_text().count("<!-- brainrc:begin"), 1)

    def test_a_linked_block_file_fails_even_when_forced(self):
        other = self.second_checkout()
        (other / "notes.md").write_text("someone else's file\n")
        (other / "AGENTS.md").symlink_to("notes.md")
        out = self.frozen(code=1, force=True)
        self.assertIn("AGENTS.md: is a link; brainrc won't write through it", out)
        self.assertEqual((other / "notes.md").read_text(), "someone else's file\n")

    def test_files_brainrc_wrote_before_are_updated_without_force(self):
        other = self.second_checkout()
        self.frozen()  # this machine now has the old files, written by brainrc
        os.chdir(self.proj)  # a teammate changes the pack and relocks
        skill = self.proj / "tools/team-pack/skills/team-deploy/SKILL.md"
        skill.write_text(skill.read_text() + "Changed.\n")
        self.apply()
        for rel in ("brainrc.lock", "tools/team-pack/skills/team-deploy/SKILL.md"):
            shutil.copy(self.proj / rel, other / rel)
        os.chdir(other)
        out = self.frozen()
        self.assertIn("UPDATE    project   .agents/skills/team-deploy/", out)
        self.assertTrue((other / ".agents/skills/team-deploy/SKILL.md").read_text().endswith("Changed.\n"))

    def test_scope_project_outside_a_project_is_an_error(self):
        os.chdir(self.proj.parent)
        self.frozen(code=2, scope="project")


class InstallCommandTest(FrozenCase):
    def test_install_without_frozen_is_apply(self):
        code, out = quiet(brainrc.main, ["brainrc", "install"])
        self.assertEqual(code, 0, out)
        self.assertTrue(self.user_lock.is_file())

    def test_scope_and_force_need_frozen(self):
        code, _ = quiet(brainrc.main, ["brainrc", "install", "--scope", "user"])
        self.assertEqual(code, 2)
        code, _ = quiet(brainrc.main, ["brainrc", "install", "--force"])
        self.assertEqual(code, 2)

    def test_lock_left_alone(self):
        self.apply()
        self.edit_lock(self.user_lock, lambda t: re.sub(r'brainrc = "[^"]*"', 'brainrc = "0.0.1"', t))
        out = self.frozen()
        self.assertIn("WARN the lock was written by brainrc 0.0.1", out)
        self.assertIn('brainrc = "0.0.1"', self.user_lock.read_text())
        self.assertEqual(lock.read(self.user_lock)["brainrc"], "0.0.1")
