"""`apply --repair` (#129): relink broken links to where an item used to be, after a moved checkout."""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, install_harnesses, quiet  # noqa: E402
from support import home_env, restore_home, rmtree, saved_home


def run(*args: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = brainrc.cli.main(["brainrc", *args])
    return code, out.getvalue()


class RepairTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        self.skill = self.home / ".claude/skills/spec-agent"

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        super().tearDown()

    def move_checkout(self) -> Path:
        old = self.repo
        new = Path(tempfile.mkdtemp()).resolve() / "moved"
        shutil.move(str(old), str(new))
        self.addCleanup(rmtree, new.parent, True)
        self.repo = new
        brainrc.config.REPO = new
        return old

    def links_into(self, root: Path) -> list[Path]:
        return [p for p in self.home.rglob("*") if p.is_symlink() and str(root) in os.readlink(p)]

    def test_a_moved_checkout_is_back_in_sync_after_repair(self):
        quiet(brainrc.cmd_sync, True)
        old = self.move_checkout()
        code, out = run("status")
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT", out)
        self.assertIn("apply --repair", out)
        code, out = run("apply", "--repair")
        self.assertEqual(code, 0, out)
        self.assertIn("REPAIR", out)
        self.assertNotIn("CONFLICT", out)
        self.assertEqual(self.links_into(old), [])
        self.assertEqual(os.readlink(self.skill), str(self.repo / "packs/gatework/skills/spec-agent"))
        self.assertTrue((self.home / ".claude/hooks/brainrc").resolve().is_dir())
        code, out = run("status")
        self.assertEqual(code, 0, out)
        self.assertIn("Everything in sync.", out)
        self.assertEqual(brainrc.doctor_findings(), [])

    def rename_skill(self):
        skills = self.repo / "packs/gatework/skills"
        new = skills / "brainrc-spec-agent-renamed"
        shutil.move(str(skills / "spec-agent"), str(new))
        md = new / "SKILL.md"
        md.write_text(md.read_text().replace("name: spec-agent\n", f"name: {new.name}\n", 1))

    def test_an_item_gone_from_the_moved_checkout_is_pruned(self):
        quiet(brainrc.cmd_sync, True)
        self.move_checkout()
        self.rename_skill()
        code, out = run("apply", "--repair")
        self.assertEqual(code, 0, out)
        self.assertIn("PRUNE", out)
        self.assertFalse(os.path.lexists(self.skill))
        self.assertTrue((self.home / ".claude/skills/brainrc-spec-agent-renamed").is_symlink())

    def test_repair_works_without_a_manifest(self):
        quiet(brainrc.cmd_sync, True)
        (self.settings_home / "harnesses.json").unlink()  # an install from before the manifest
        self.move_checkout()
        self.rename_skill()
        code, out = run("apply", "--repair")
        self.assertEqual(code, 0, out)
        self.assertFalse(os.path.lexists(self.skill))  # pruned: its old root was inferred
        self.assertIn("Everything in sync.", run("status")[1])

    def test_status_repair_writes_nothing(self):
        quiet(brainrc.cmd_sync, True)
        old = self.move_checkout()
        before = sorted(self.links_into(old))
        code, out = run("status", "--repair")
        self.assertEqual(code, 0, out)
        self.assertIn("REPAIR", out)
        self.assertEqual(sorted(self.links_into(old)), before)

    def test_a_broken_link_to_another_item_stays_a_conflict(self):
        self.skill.parent.mkdir(parents=True, exist_ok=True)
        self.skill.symlink_to(self.home / "gone/somewhere-else")
        code, out = run("apply", "--repair")
        self.assertEqual(code, 1)
        self.assertIn("CONFLICT", out)
        self.assertEqual(os.readlink(self.skill), str(self.home / "gone/somewhere-else"))

    def test_a_working_link_to_the_users_own_copy_stays_a_conflict(self):
        mine = self.home / "mine/skills/spec-agent"
        mine.mkdir(parents=True)
        self.skill.parent.mkdir(parents=True, exist_ok=True)
        self.skill.symlink_to(mine)
        code, out = run("apply", "--repair")
        self.assertEqual(code, 1)
        self.assertEqual(os.readlink(self.skill), str(mine))
        self.assertNotIn("apply --repair` relinks", out)

    def test_doctor_suggests_repair_for_a_moved_checkout(self):
        quiet(brainrc.cmd_sync, True)
        self.move_checkout()
        fixes = [fix for _, _, fix in brainrc.doctor_findings()]
        self.assertTrue(any(fix.endswith("apply --repair") for fix in fixes), fixes)

    def test_repair_with_only_touches_that_harness(self):
        quiet(brainrc.cmd_sync, True)
        old = self.move_checkout()
        code, out = run("apply", "--repair", "--only", "codex")
        self.assertEqual(code, 0, out)
        self.assertFalse(any(".codex" in str(p) for p in self.links_into(old)))
        self.assertTrue(any(".claude" in str(p) for p in self.links_into(old)))

    def test_the_users_live_links_survive_a_repair_of_their_broken_one(self):
        quiet(brainrc.cmd_sync, True)
        notes = self.home / "dotfiles/skills/my-notes"
        notes.mkdir(parents=True)
        (notes / "SKILL.md").write_text("x\n")
        mine = self.home / ".claude/skills/my-notes"
        mine.symlink_to(notes)
        self.skill.unlink()
        self.skill.symlink_to(self.home / "dotfiles/skills/spec-agent")  # the user's own, broken
        code, out = run("apply", "--repair")
        self.assertEqual(code, 0, out)
        self.assertNotIn("PRUNE", out)
        self.assertEqual(os.readlink(mine), str(notes))
        self.assertEqual(os.readlink(self.skill), str(self.repo / "packs/gatework/skills/spec-agent"))

    def test_a_shallow_broken_link_never_makes_home_a_root(self):
        quiet(brainrc.cmd_sync, True)
        (self.home / "skills/my-notes").mkdir(parents=True)
        mine = self.home / ".claude/skills/my-notes"
        mine.symlink_to(self.home / "skills/my-notes")  # a live link of the user's
        self.skill.unlink()
        self.skill.symlink_to(self.home / "skills/spec-agent")  # broken: its derived root is ~
        (trusted, prune), _ = quiet(brainrc.cli._old_roots, brainrc.sources(), [self.repo])
        self.assertNotIn(self.home, trusted + prune)
        code, out = run("apply", "--repair")
        self.assertEqual(code, 0, out)
        self.assertTrue(mine.is_symlink())

    def test_manifest_roots_too_broad_to_trust_are_ignored(self):
        quiet(brainrc.cmd_sync, True)
        manifest = self.settings_home / "harnesses.json"
        data = __import__("json").loads(manifest.read_text())
        data["roots"] += [str(self.home), "/"]
        manifest.write_text(__import__("json").dumps(data))
        code, out = run("status", "--repair")
        self.assertEqual(code, 0, out)
        self.assertIn("ignored root", out)
        srcs = brainrc.sources()
        (trusted, _), _ = quiet(brainrc.cli._old_roots, srcs, [s.root for s in srcs])
        self.assertEqual(trusted, [])


if __name__ == "__main__":
    unittest.main()
