"""Git packs pinned to a commit (#288): apply and install keep each git pack at the commit
brainrc.lock records, and only `brainrc update <pack>` moves it, printing the commits and the
installed files that change first. Gatework, the default git pack, is the main case."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import rmtree  # noqa: E402
from test_brainrc import git, quiet  # noqa: E402
from test_lock import GitLockCase, rev  # noqa: E402

from brainrc import lock  # noqa: E402
import brainrc  # noqa: E402


class PinCase(GitLockCase):
    def setUp(self):
        super().setUp()
        self.work = self.tmp / "gatework-work"
        self.clone = self.settings_home / "packs/gatework"

    def commit(self, message: str, **files: str) -> str:
        """Commit files (path with `__` for `/` -> text, or None to delete) on main and push it."""
        for name, text in files.items():
            path = self.work / name.replace("__", "/")
            if text is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
        git("add", "-A", cwd=self.work)
        git("commit", "-qm", message, cwd=self.work)
        git("push", "-q", str(self.bare), "main", cwd=self.work)
        return rev(self.bare, "main")

    def follow_main(self) -> None:
        """Gatework with no `ref`: it follows the remote's default branch, as #288 describes."""
        (self.repo / "packs.toml").write_text(f'[gatework]\ngit = "{self.url}"\n')

    def update(self, *names: str, code: int = 0) -> str:
        got, out = quiet(brainrc.cmd_update, list(names))
        self.assertEqual(got, code, out)
        return out

    def pin(self) -> str:
        return lock.read(self.user_lock)["packs"]["gatework"]["commit"]


class DefaultBranchPinTest(PinCase):
    def setUp(self):
        super().setUp()
        self.follow_main()
        self.apply()
        self.a = rev(self.bare, "main")

    def test_the_lock_records_the_commit_the_default_branch_resolved_to(self):
        gw = lock.read(self.user_lock)["packs"]["gatework"]
        self.assertEqual((gw["ref"], gw["commit"]), ("HEAD", self.a))

    def test_a_fresh_machine_installs_the_pinned_commit_not_the_branch_tip(self):
        b = self.commit("v3", **{"skills__brainrc-later__SKILL.md": SKILL("brainrc-later")})
        rmtree(self.clone)  # a teammate's machine: nothing fetched yet
        out = self.apply()
        self.assertIn(f"(default branch, locked at {self.a[:12]})", out)
        self.assertEqual(self.pin(), self.a)
        self.assertNotEqual(self.a, b)
        self.assertFalse((self.home / ".claude/skills/brainrc-later").exists())

    def test_a_clone_moved_by_hand_goes_back_to_the_pin(self):
        b = self.commit("v3", **{"skills__brainrc-later__SKILL.md": SKILL("brainrc-later")})
        git("fetch", "-q", "--depth", "1", self.url, "main", cwd=self.clone)
        git("checkout", "-q", "--detach", "FETCH_HEAD", cwd=self.clone)
        self.assertEqual(rev(self.clone, "HEAD"), b)
        out = self.status()
        self.assertIn(f"locked at {self.a[:12]}", out)
        self.assertEqual(rev(self.clone, "HEAD"), b)  # status writes nothing
        self.apply()
        self.assertEqual(rev(self.clone, "HEAD"), self.a)
        self.assertEqual(self.pin(), self.a)

    def test_update_moves_the_pin_and_shows_commits_and_files_first(self):
        self.commit("Add brainrc-later", **{"skills__brainrc-later__SKILL.md": SKILL("brainrc-later")})
        work_skill = "skills/brainrc-work/SKILL.md"
        b = self.commit("Edit brainrc-work and drop the aws skill", **{
            work_skill.replace("/", "__"): (self.work / work_skill).read_text() + "More.\n",
            "skills__brainrc-aws__SKILL.md": None})
        out = self.update("gatework")
        lines = out.splitlines()
        moved = lines.index(f"MOVED     gatework  HEAD: {self.a[:12]} -> {b[:12]}  (user scope)")
        report = lines[moved + 1:moved + 6]
        self.assertEqual([line.split()[0] for line in report], ["commit", "commit", "removed", "added", "changed"])
        self.assertTrue(report[0].endswith("Edit brainrc-work and drop the aws skill"), report)
        self.assertTrue(report[1].endswith("Add brainrc-later"), report)
        self.assertTrue(report[2].endswith("skills/brainrc-aws/SKILL.md"), report)  # sorted by path
        self.assertTrue(report[3].endswith("skills/brainrc-later/SKILL.md"), report)
        self.assertTrue(report[4].endswith(work_skill), report)
        linked = next(i for i, line in enumerate(lines) if line.startswith("CREATE") and "brainrc-later" in line)
        self.assertLess(moved, linked)  # the diff comes before anything is written
        self.assertEqual(self.pin(), b)
        self.assertTrue((self.home / ".claude/skills/brainrc-later").is_symlink())

    def test_update_with_nothing_new_says_so(self):
        out = self.update("gatework")
        self.assertIn(f"CURRENT   gatework  HEAD at {self.a[:12]}, no change  (user scope)", out)
        self.assertEqual(self.pin(), self.a)

    def test_update_names_only_git_packs(self):
        out = self.update("acme", code=2)
        self.assertIn("ERROR pack acme: not a git pack here (git packs: gatework)", out)
        self.assertNotIn("FETCH", out)

    def test_a_rewritten_branch_is_named_as_such(self):
        git("reset", "-q", "--hard", "HEAD~1", cwd=self.work)
        (self.work / "README.md").write_text("Rewritten.\n")
        git("commit", "-qam", "rewrite", cwd=self.work)
        git("push", "-qf", str(self.bare), "main", cwd=self.work)
        out = self.update()
        self.assertIn(f"{self.a[:12]} isn't in the last 50 commits of HEAD", out)
        self.assertEqual(self.pin(), rev(self.bare, "main"))

    def test_a_terminal_escape_in_a_commit_subject_is_not_printed(self):
        self.commit("bad \x1b]0;owned\x07 subject", **{"skills__brainrc-later__SKILL.md": SKILL("brainrc-later")})
        out = self.update()
        self.assertNotIn("\x1b", out)
        self.assertIn("bad ?]0;owned? subject", out)

    def test_a_new_ref_is_pinned_without_a_false_history_warning(self):
        (self.repo / "packs.toml").write_text(f'[gatework]\ngit = "{self.url}"\nref = "v1"\n')
        out = self.update()
        self.assertIn("a new `git` or `ref` since brainrc.lock", out)
        self.assertNotIn("isn't in the last", out)
        self.assertEqual(self.pin(), rev(self.bare, "v1"))

    @unittest.skipIf(os.name == "nt", "Windows file names can't hold control characters")
    def test_a_terminal_escape_in_a_file_name_is_not_printed(self):
        self.commit("odd name", **{"skills__brainrc-later__SKILL.md": SKILL("brainrc-later"),
                                   "skills__brainrc-later__x\x1b[2Jy.md": "x\n"})
        out = self.update()
        self.assertNotIn("\x1b", out)
        self.assertIn("skills/brainrc-later/x?[2Jy.md", out)

    def test_a_broken_project_config_still_updates_the_user_scope(self):
        b = self.commit("v3", **{"skills__brainrc-later__SKILL.md": SKILL("brainrc-later")})
        self.manifest("[packs.gatework\n")
        got, out = quiet(brainrc.cmd_update, [])
        self.assertIn("WARN the project's packs aren't updated", out)
        self.assertEqual(self.pin(), b)

    def test_a_pinned_commit_that_cant_be_fetched_names_update(self):
        rmtree(self.clone)
        (self.repo / "packs.toml").write_text(f'[gatework]\ngit = "{(self.tmp / "gone.git").as_uri()}"\n')
        lock_data = lock.read(self.user_lock)
        lock_data["packs"]["gatework"]["git"] = (self.tmp / "gone.git").as_uri()
        lock.write(self.user_lock, lock_data)
        got, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(got, 1, out)
        self.assertIn("update gatework` moves the pin.", out)

    def test_a_failed_update_leaves_apply_on_the_pin(self):
        self.commit("v3", **{"skills__brainrc-later__SKILL.md": SKILL("brainrc-later")})
        (self.repo / "packs.toml").write_text(f'[gatework]\ngit = "{(self.tmp / "gone.git").as_uri()}"\n')
        out = self.update(code=1)
        self.assertIn("Nothing applied", out)
        self.follow_main()
        self.apply()
        self.assertEqual(self.pin(), self.a)


class SecondPackTest(PinCase):
    def test_update_one_pack_leaves_the_other_pinned(self):
        team_work = self.tmp / "team-work"
        (team_work / "skills/team-x").mkdir(parents=True)
        (team_work / "pack.toml").write_text('name = "team"\nprefix = "team-"\nrequires_core = ">=0"\n')
        (team_work / "skills/team-x/SKILL.md").write_text(SKILL("team-x"))
        for args in (("init", "-q", "-b", "main"), ("add", "-A"), ("commit", "-qm", "team 1")):
            git(*args, cwd=team_work)
        team_bare = self.tmp / "team.git"
        git("clone", "-q", "--bare", str(team_work), str(team_bare))
        (self.repo / "packs.local.toml").write_text(f'[team]\ngit = "{team_bare.as_uri()}"\nref = "main"\n')
        self.apply()
        team_a = lock.read(self.user_lock)["packs"]["team"]["commit"]
        (team_work / "README.md").write_text("Newer.\n")
        git("add", "-A", cwd=team_work)
        git("commit", "-qm", "team 2", cwd=team_work)
        git("push", "-q", str(team_bare), "main", cwd=team_work)
        self.move_tag("v1", "v2")
        out = self.update("gatework")
        self.assertIn("MOVED     gatework", out)
        self.assertNotIn("FETCH     team", out)
        locked = lock.read(self.user_lock)["packs"]
        self.assertEqual(locked["team"]["commit"], team_a)
        self.assertEqual(locked["gatework"]["commit"], rev(self.bare, "v2"))


def SKILL(name: str) -> str:
    return f"---\nname: {name}\ndescription: Added later.\n---\nBody.\n"


if __name__ == "__main__":
    unittest.main()
