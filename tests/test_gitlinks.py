"""Git's stand-ins for links (#120): with core.symlinks off, git checks a link out as a plain file
holding its target. Copy mode copies what one points to, and validate reads a Markdown link through
one in copy mode. The checkout here records the link in git's index without making one, so the test
runs the same on a machine that can't make symlinks."""
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import rmtree  # noqa: E402

from brainrc import copies, gitlinks, validate  # noqa: E402
from brainrc.config import ConfigError  # noqa: E402


def git(root: Path, *args: str, stdin: str | None = None) -> str:
    return subprocess.run(["git", "-C", str(root), *args], input=stdin, capture_output=True, text=True,
                          check=True).stdout.strip()


def record_link(root: Path, rel: str, target: str) -> Path:
    """Record rel as a link to target in git's index and leave git's stand-in for it on disk."""
    sha = git(root, "hash-object", "-w", "--stdin", stdin=target)
    git(root, "update-index", "--add", "--cacheinfo", f"120000,{sha},{rel}")
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(target.encode())
    return path


@unittest.skipUnless(shutil.which("git"), "needs git")
class GitLinksTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, self.root)
        git(self.root, "init", "-q")
        (self.root / "agents").mkdir()
        (self.root / "agents/acme-analyst.md").write_text("Analyst.\n")
        self.skill = self.root / "skills/acme-work"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("See [the analyst](roles/acme-analyst.md).\n")
        git(self.root, "add", "agents", "skills")
        self.roles = record_link(self.root, "skills/acme-work/roles", "../../agents")

    def test_a_stand_in_is_found_and_read_through(self):
        self.assertEqual(gitlinks.stand_ins(self.skill), {self.roles: self.root / "agents"})
        self.assertEqual(gitlinks.resolve(self.roles / "acme-analyst.md"), self.root / "agents/acme-analyst.md")
        self.assertEqual(gitlinks.resolve(self.skill / "SKILL.md"), self.skill / "SKILL.md")

    def test_a_windows_target_with_backslashes_is_read(self):
        self.roles.write_bytes(b"..\\..\\agents")
        self.assertEqual(gitlinks.stand_ins(self.skill), {self.roles: self.root / "agents"})

    def test_a_plain_file_git_does_not_record_as_a_link_is_left_alone(self):
        (self.skill / "notes").write_text("../../agents")
        git(self.root, "add", "skills/acme-work/notes")
        self.assertNotIn(self.skill / "notes", gitlinks.stand_ins(self.skill))

    def test_a_target_outside_the_checkout_or_absolute_is_not_followed(self):
        for target in ("../../../outside", "/etc", "C:/Windows", "../../missing", ".", "..", "../.."):
            with self.subTest(target=target):
                self.roles.write_text(target)
                self.assertEqual(gitlinks.stand_ins(self.skill), {})

    def test_outside_a_checkout_there_are_none(self):
        plain = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, plain)
        (plain / "roles").write_text("../agents")
        self.assertEqual(gitlinks.stand_ins(plain), {})

    def test_copy_mode_copies_what_the_stand_in_points_to(self):
        home = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, home)
        with mock.patch.dict(os.environ, {"BRAINRC_HOME": str(home / "settings"), copies.ENV: "copy"}):
            dest = home / "skills/acme-work"
            dest.parent.mkdir()
            copies.place("claude", dest, self.skill)
            self.assertTrue((dest / "roles").is_dir())
            self.assertFalse((dest / "roles").is_symlink())
            self.assertEqual((dest / "roles/acme-analyst.md").read_text(), "Analyst.\n")
            self.assertFalse(copies.edited(dest, copies.read()[copies.key(dest)]))

    def test_a_change_behind_a_stand_in_changes_the_source_digest(self):
        before = copies.digest(self.skill)
        (self.root / "agents/acme-analyst.md").write_text("Analyst, revised.\n")
        self.assertNotEqual(copies.digest(self.skill), before)

    def test_stand_ins_that_point_at_each_other_stop_the_copy(self):
        (self.root / "other").mkdir()
        (self.root / "other/note.md").write_text("Note.\n")
        git(self.root, "add", "other")
        record_link(self.root, "skills/acme-work/more", "../../other")
        record_link(self.root, "other/back", "../skills/acme-work")
        home = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, home)
        with mock.patch.dict(os.environ, {"BRAINRC_HOME": str(home / "settings"), copies.ENV: "copy"}):
            self.assertIsNotNone(copies.digest(self.skill))  # the digest stops at the loop too
            with self.assertRaisesRegex(ConfigError, "point at each other"):
                copies.place("claude", home / "acme-work", self.skill)
        self.assertFalse(os.path.lexists(home / "acme-work"))

    def test_a_worktree_finds_its_index_through_the_git_file(self):
        tree = Path(tempfile.mkdtemp()).resolve() / "tree"
        self.addCleanup(rmtree, tree.parent)
        git(self.root, "-c", "user.name=acme", "-c", "user.email=acme@example.com", "commit", "-qm", "init")
        git(self.root, "-c", "core.symlinks=false", "worktree", "add", "-q", str(tree))
        roles = tree / "skills/acme-work/roles"
        if roles.is_symlink():  # this git made the link anyway: put back the stand-in it would write
            roles.unlink()
            roles.write_text("../../agents")
        self.assertTrue((tree / ".git").is_file())
        self.assertEqual(gitlinks.stand_ins(tree / "skills"), {roles: tree / "agents"})

    def references(self, mode: str) -> list[str]:
        src = types.SimpleNamespace(root=self.root, prefix="", rel=lambda p: p.relative_to(self.root).as_posix())
        with mock.patch.dict(os.environ, {copies.ENV: mode}):
            return validate._check_references(src, self.skill / "SKILL.md", set(), set(), tags=False)

    def test_validate_reads_a_link_through_a_stand_in_in_copy_mode(self):
        self.assertEqual(self.references("copy"), [])

    def test_validate_names_the_stand_in_in_link_mode(self):
        errors = self.references("symlink")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("git checked out as a plain file", errors[0])
        self.assertIn('link_mode = "copy"', errors[0])

    def test_a_link_that_is_broken_through_the_stand_in_is_still_broken(self):
        (self.skill / "SKILL.md").write_text("See [the architect](roles/acme-architect.md).\n")
        self.assertEqual(self.references("copy"), ["skills/acme-work/SKILL.md: broken link `roles/acme-architect.md`"])


if __name__ == "__main__":
    unittest.main()
