"""brainrc.lock with a commit and a SHA-256 per file (#283). Gatework, a default git pack, is the
main case: a bare user-scope install with only Gatework is fully locked."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import rmtree  # noqa: E402
from test_brainrc import DEFAULT_PACK, git, quiet  # noqa: E402
from test_project_scope import ProjectCase, gatework_remote, make_team_pack, use_git_gatework  # noqa: E402

from brainrc import lock, schema  # noqa: E402
import brainrc  # noqa: E402


def rev(bare: Path, ref: str) -> str:
    return subprocess.run(["git", "rev-parse", f"{ref}^{{commit}}"], cwd=bare, capture_output=True, text=True,
                          check=True).stdout.strip()


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class GitLockCase(ProjectCase):
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.url = gatework_remote(self.tmp)
        self.bare = self.tmp / "gatework.git"
        use_git_gatework(self.repo, self.url, "v1")
        self.user_lock = self.settings_home / "brainrc.lock"

    def tearDown(self):
        super().tearDown()
        rmtree(self.tmp)

    def move_tag(self, tag: str, to: str) -> None:
        git("tag", "-f", tag, rev(self.bare, to), cwd=self.bare)


class UserLockTest(GitLockCase):
    def test_gatework_alone_is_fully_locked(self):
        self.apply()
        data = lock.read(self.user_lock)
        self.assertEqual(schema.errors(data, schema.load("brainrc.lock")), [])
        self.assertEqual(data["scope"], "user")
        gw = data["packs"]["gatework"]
        self.assertEqual((gw["git"], gw["ref"], gw["commit"]), (self.url, "v1", rev(self.bare, "v1")))
        clone = self.settings_home / "packs/gatework"
        for rel in ("pack.toml", "validator.py", "skills/brainrc-work/SKILL.md", "agents/brainrc-analyst.md",
                    "skills/brainrc-gatework/references/campaign.md"):
            self.assertEqual(gw["files"][rel], sha(clone / rel), rel)
        # A linked directory is hashed as the files it shows: roles/ -> ../../agents
        self.assertEqual(gw["files"]["skills/brainrc-gatework/roles/brainrc-analyst.md"],
                         sha(DEFAULT_PACK / "agents/brainrc-analyst.md"))
        self.assertNotIn("README.md", gw["files"])  # not installed
        self.assertNotIn("skills/brainrc-new/SKILL.md", gw["files"])  # v2 only

    def test_a_second_apply_leaves_the_lock_byte_identical(self):
        self.apply()
        first = self.user_lock.read_bytes()
        self.apply()
        self.assertEqual(self.user_lock.read_bytes(), first)
        self.assertTrue(first.startswith(b"# brainrc.lock: written by brainrc."))
        self.assertNotIn(str(self.home).encode(), first)

    def test_status_writes_no_lock(self):
        self.apply()
        self.user_lock.unlink()
        self.status()
        self.assertFalse(self.user_lock.exists())

    def test_a_moved_tag_is_relocked_by_update_only(self):
        self.apply()
        old_text = self.user_lock.read_text()
        a, b = rev(self.bare, "v1"), rev(self.bare, "v2")
        self.move_tag("v1", "v2")
        out = self.status()
        self.assertNotIn("MOVED", out)  # status never fetches, so it can't know yet
        code, out = quiet(brainrc.cmd_update)
        self.assertEqual(code, 0, out)
        self.assertIn(f"MOVED     gatework  v1: {a[:12]} -> {b[:12]}  (user scope)", out)
        self.assertEqual(lock.read(self.user_lock)["packs"]["gatework"]["commit"], b)
        self.user_lock.write_text(old_text)  # e.g. the lock from before, restored
        out = self.status()
        self.assertIn(f"(v1, locked at {a[:12]})", out)  # apply goes back to the pin, not forward
        self.apply()
        self.assertEqual(lock.read(self.user_lock)["packs"]["gatework"]["commit"], a)

    def test_a_changed_ref_is_not_a_move(self):
        self.apply()
        (self.repo / "packs.local.toml").write_text('[gatework]\nref = "v2"\n')
        out = self.apply()
        self.assertNotIn("MOVED", out)
        gw = lock.read(self.user_lock)["packs"]["gatework"]
        self.assertEqual((gw["ref"], gw["commit"]), ("v2", rev(self.bare, "v2")))
        self.assertIn("skills/brainrc-new/SKILL.md", gw["files"])

    def test_a_path_override_is_locked_as_a_path_with_hashes(self):
        checkout = self.home / "src/gatework"
        shutil.copytree(DEFAULT_PACK, checkout, symlinks=True)
        (self.repo / "packs.local.toml").write_text(f'[gatework]\npath = "{checkout.as_posix()}"\n')
        self.apply()
        gw = lock.read(self.user_lock)["packs"]["gatework"]
        self.assertEqual(gw["path"], "~/src/gatework")
        self.assertNotIn("commit", gw)
        self.assertNotIn("git", gw)
        before = gw["files"]["skills/brainrc-work/SKILL.md"]
        skill = checkout / "skills/brainrc-work/SKILL.md"
        skill.write_text(skill.read_text() + "Changed.\n")
        self.apply()
        after = lock.read(self.user_lock)["packs"]["gatework"]["files"]["skills/brainrc-work/SKILL.md"]
        self.assertNotEqual(after, before)
        self.assertEqual(after, sha(skill))

    def test_profile_and_exclude_shape_the_files(self):
        (self.repo / "brainrc.local.toml").write_text('exclude = ["skills/brainrc-aws"]\n')
        self.apply()
        files = lock.read(self.user_lock)["packs"]["gatework"]["files"]
        self.assertFalse(any(f.startswith("skills/brainrc-aws/") for f in files))
        (self.repo / "brainrc.local.toml").write_text('profile = "minimal"\n')
        self.apply()
        files = lock.read(self.user_lock)["packs"]["gatework"]["files"]
        self.assertEqual(sorted(files), ["pack.toml", "validator.py"])

    def test_a_disabled_pack_is_not_in_the_lock(self):
        (self.repo / "packs.local.toml").write_text("[gatework]\nenabled = false\n")
        self.apply()
        self.assertNotIn("packs", lock.read(self.user_lock))


class ProjectLockTest(GitLockCase):
    def test_the_project_lock_records_each_pack_and_every_output(self):
        make_team_pack(self.proj / "tools/team-pack")
        self.manifest('[packs.team]\npath = "tools/team-pack"\n')
        self.apply()
        data = lock.read(self.proj / "brainrc.lock")
        self.assertEqual(schema.errors(data, schema.load("brainrc.lock")), [])
        gw, team = data["packs"]["gatework"], data["packs"]["team"]
        self.assertEqual((gw["ref"], gw["commit"]), ("v1", rev(self.bare, "v1")))
        self.assertEqual(team, {"path": "tools/team-pack", "files": team["files"], "permissions": {}})
        self.assertIn("rules/50-team.md", team["files"])
        self.assertNotIn("agents/team-reviewer.md", team["files"])  # project scope installs no agents yet
        self.assertEqual(data["outputs"][".agents/skills/team-deploy/SKILL.md"],
                         team["files"]["skills/team-deploy/SKILL.md"])

    def test_a_changed_pack_file_changes_its_hash_and_nothing_else(self):
        make_team_pack(self.proj / "tools/team-pack")
        self.manifest('[packs.team]\npath = "tools/team-pack"\n')
        self.apply()
        before = lock.read(self.proj / "brainrc.lock")
        skill = self.proj / "tools/team-pack/skills/team-deploy/SKILL.md"
        skill.write_text(skill.read_text() + "Changed.\n")
        self.apply()
        after = lock.read(self.proj / "brainrc.lock")
        changed = {k for k in after["packs"]["team"]["files"]
                   if after["packs"]["team"]["files"][k] != before["packs"]["team"]["files"][k]}
        self.assertEqual(changed, {"skills/team-deploy/SKILL.md"})
        self.assertEqual(after["packs"]["gatework"], before["packs"]["gatework"])

    def test_a_moved_tag_under_the_clone_goes_back_to_the_pin(self):
        self.manifest()
        self.apply()
        teammates = (self.proj / "brainrc.lock").read_text()
        a, b = rev(self.bare, "v1"), rev(self.bare, "v2")
        self.move_tag("v1", "v2")
        clone = next((self.settings_home / "project-packs").iterdir())
        git("fetch", "-q", "--depth", "1", self.url, "v1", cwd=clone)  # this machine saw the new tag
        git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=clone)
        out = self.status()
        self.assertIn(f"(v1, locked at {a[:12]})", out)
        self.assertEqual((self.proj / "brainrc.lock").read_text(), teammates)
        out = self.apply()
        self.assertNotIn("MOVED", out)
        self.assertNotIn("brainrc-new", self.skills())
        self.assertEqual((self.proj / "brainrc.lock").read_text(), teammates)
        code, out = quiet(brainrc.cmd_update, ["gatework"])
        self.assertEqual(code, 0, out)
        self.assertIn(f"MOVED     gatework  v1: {a[:12]} -> {b[:12]}  (project, brainrc.toml)", out)
        self.assertIn("brainrc-new", self.skills())
        self.assertEqual(lock.read(self.proj / "brainrc.lock")["packs"]["gatework"]["commit"], b)


class CleanUrlTest(unittest.TestCase):
    def test_credentials_never_reach_the_lock(self):
        self.assertEqual(lock.clean_url("https://bot:tok@example.com/a.git"), "https://example.com/a.git")
        self.assertEqual(lock.clean_url("https://tok@example.com/a.git"), "https://example.com/a.git")
        self.assertEqual(lock.clean_url("ssh://git:pw@example.com/a.git"), "ssh://git@example.com/a.git")
        self.assertEqual(lock.clean_url("git@example.com:a/b.git"), "git@example.com:a/b.git")
        self.assertEqual(lock.clean_url("file:///srv/a.git"), "file:///srv/a.git")


if __name__ == "__main__":
    unittest.main()
