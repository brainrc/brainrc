"""A pack from a folder of a git repo (#121): `subdir` next to `git` and `ref`, so one repo
(brainrc/packs) can hold many packs. Local bare repos only, never github.com."""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import git, quiet  # noqa: E402
from test_frozen import FrozenCase, tree  # noqa: E402
from test_lock import rev  # noqa: E402

from brainrc import lock, schema  # noqa: E402
from brainrc.sources import clone_root, in_clone, subdir  # noqa: E402
from brainrc.config import ConfigError  # noqa: E402
import brainrc  # noqa: E402


def skill(root: Path, name: str, body: str = "Body.") -> None:
    d = root / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name} for tests.\n---\n{body}\n")


def monorepo(tmp: Path) -> str:
    """A bare repo standing in for brainrc/packs: python/ and rust/ packs, tagged v1; v2 changes
    python's skill. Returns its URL."""
    work = tmp / "packs-work"
    for name in ("python", "rust"):
        root = work / name
        root.mkdir(parents=True)
        (root / "pack.toml").write_text(f'name = "{name}"\nprefix = "{name}-"\nrequires_core = ">=0.1"\n')
        skill(root, f"{name}-validate")
    (work / "README.md").write_text("Official packs, one per folder.\n")
    git("init", "-q", "-b", "main", cwd=work)
    git("add", "-A", cwd=work)
    git("commit", "-qm", "v1", cwd=work)
    git("tag", "v1", cwd=work)
    (work / "python/skills/python-validate/SKILL.md").write_text(
        "---\nname: python-validate\ndescription: python-validate for tests.\n---\nNew in v2.\n")
    git("commit", "-qam", "v2", cwd=work)
    git("tag", "v2", cwd=work)
    git("clone", "-q", "--bare", str(work), str(tmp / "packs.git"))
    return (tmp / "packs.git").as_uri()


class SubdirCase(FrozenCase):
    def setUp(self):
        super().setUp()
        self.packs_url = monorepo(self.tmp)
        self.packs_bare = self.tmp / "packs.git"

    def use(self, **subdirs: str) -> None:
        """Enable each key from the monorepo at its folder, ref v1, in packs.local.toml."""
        (self.repo / "packs.local.toml").write_text("".join(
            f'[{key}]\ngit = "{self.packs_url}"\nref = "v1"\nsubdir = "{sub}"\n\n' for key, sub in subdirs.items()))


class SubdirValueTest(SubdirCase):
    def test_valid_folders_are_kept_without_a_trailing_slash(self):
        cfg = {"git": "x"}
        self.assertEqual(subdir(cfg), "")
        for value, want in (("python", "python"), ("packs/python/", "packs/python"), ("a.b", "a.b")):
            self.assertEqual(subdir({**cfg, "subdir": value}), want)

    def test_a_folder_outside_the_repo_or_not_a_folder_is_refused(self):
        for value in ("", "/", "/abs", "../up", "a/../b", "a//b", "./a", "-x", "a\\b", "C:/x", 3):
            with self.subTest(value=value), self.assertRaisesRegex(ConfigError, "must be a folder inside the repo"):
                subdir({"git": "x", "subdir": value}, "packs.toml", "py")

    def test_subdir_without_git_is_refused(self):
        with self.assertRaisesRegex(ConfigError, r"packs.toml \[py\]: `subdir` goes with `git`"):
            subdir({"path": "~/p", "subdir": "python"}, "packs.toml", "py")

    def test_clone_root_and_in_clone_are_inverse(self):
        cfg = {"git": "x", "subdir": "packs/python"}
        clone = Path("/h/packs/py")
        self.assertEqual(in_clone(cfg, clone), Path("/h/packs/py/packs/python"))
        self.assertEqual(clone_root(cfg, in_clone(cfg, clone)), clone)
        self.assertEqual(clone_root({"git": "x"}, clone), clone)


class SubdirApplyTest(SubdirCase):
    def test_two_packs_from_one_repo_install_and_lock_their_folder(self):
        self.use(python="python", rust="rust")
        self.apply()
        for name in ("python-validate", "rust-validate"):
            self.assertTrue((self.home / ".claude/skills" / name / "SKILL.md").is_file(), name)
        data = lock.read(self.user_lock)
        self.assertEqual(schema.errors(data, schema.load("brainrc.lock")), [])
        self.assertEqual(data["version"], 3)
        py = data["packs"]["python"]
        self.assertEqual((py["git"], py["ref"], py["subdir"], py["commit"]),
                         (self.packs_url, "v1", "python", rev(self.packs_bare, "v1")))
        self.assertEqual(sorted(py["files"]), ["pack.toml", "skills/python-validate/SKILL.md"])
        self.assertNotIn("README.md", py["files"])  # the repo's, not the pack's
        self.assertIn('subdir = "python"\ncommit = ', self.user_lock.read_text())

    def test_a_lock_without_subdir_stays_version_2(self):
        self.apply()  # Gatework alone, from its repo root
        self.assertIn(b"\nversion = 2\n", self.user_lock.read_bytes())
        self.assertNotIn(b"subdir", self.user_lock.read_bytes())

    def test_a_missing_folder_fails_apply_and_names_it(self):
        self.use(python="pyhton")
        out = self.apply(1)
        self.assertIn("no folder `pyhton`", out)
        self.assertFalse((self.settings_home / "packs/python").exists())  # the new clone isn't kept

    def test_a_folder_that_links_out_of_the_repo_is_refused(self):
        work = self.tmp / "packs-work"
        os.symlink("../..", work / "escape")
        git("add", "escape", cwd=work)
        git("commit", "-qm", "link", cwd=work)
        git("tag", "v3", cwd=work)
        git("push", "-q", str(self.packs_bare), "v3", cwd=work)
        (self.repo / "packs.local.toml").write_text(f'[x]\ngit = "{self.packs_url}"\nref = "v3"\nsubdir = "escape"\n')
        self.assertIn("links outside the repo", self.apply(1))

    def test_changing_the_folder_reuses_the_clone_and_relocks(self):
        self.use(python="python")
        self.apply()
        self.use(python="rust")
        out = self.apply()
        self.assertNotIn("FETCH", out)  # same URL and ref: no new fetch
        self.assertEqual(lock.read(self.user_lock)["packs"]["python"]["subdir"], "rust")

    def test_status_shows_the_folder_it_would_fetch(self):
        self.use(python="python")
        got, out = quiet(brainrc.cmd_sync, False)
        self.assertIn(f"{self.packs_url} (v1, folder python)", out)

    def test_a_local_git_without_subdir_drops_the_default_packs_folder(self):
        (self.repo / "packs.toml").write_text(f'[gatework]\ngit = "{self.url}"\nref = "v1"\nsubdir = "nope"\n')
        (self.repo / "packs.local.toml").write_text(f'[gatework]\ngit = "{self.url}"\n')
        self.apply()  # the local `git` replaces the default's origin, its `subdir` included


class TakeOverTest(SubdirCase):
    """#318: an official pack takes over a skill Gatework still ships; excluding Gatework's copy is
    what lets the two be enabled together until Gatework drops it."""

    def setUp(self):
        super().setUp()
        work = self.tmp / "packs-work"
        root = work / "kubernetes"
        root.mkdir()
        (root / "pack.toml").write_text('name = "kubernetes"\nprefix = "brainrc-"\nid = "brainrc/kubernetes"\n'
                                        'requires_core = ">=0.1"\n')
        skill(root, "brainrc-kubernetes", "From the kubernetes pack.")
        git("add", "-A", cwd=work)
        git("commit", "-qm", "kubernetes", cwd=work)
        git("tag", "k1", cwd=work)
        git("push", "-q", str(self.packs_bare), "k1", cwd=work)
        (self.repo / "packs.local.toml").write_text(
            f'[kubernetes]\ngit = "{self.packs_url}"\nref = "k1"\nsubdir = "kubernetes"\n')

    def test_both_copies_collide(self):
        self.assertIn("skill `brainrc-kubernetes` is defined in both gatework and kubernetes", self.apply(1))

    def test_excluding_gateworks_copy_installs_the_packs(self):
        (self.repo / "brainrc.local.toml").write_text('exclude = ["gatework:skills/brainrc-kubernetes"]\n')
        self.apply()
        self.assertIn("From the kubernetes pack.",
                      (self.home / ".claude/skills/brainrc-kubernetes/SKILL.md").read_text())
        files = lock.read(self.user_lock)["packs"]
        self.assertNotIn("skills/brainrc-kubernetes/SKILL.md", files["gatework"]["files"])
        self.assertIn("skills/brainrc-kubernetes/SKILL.md", files["kubernetes"]["files"])


class SubdirFrozenTest(SubdirCase):
    def test_two_machines_get_identical_files_from_one_lock(self):
        self.use(python="python", rust="rust")
        self.apply()
        text, first = self.user_lock.read_text(), tree(self.home / ".claude")
        self.move_packs_tag()  # the ref moves; the lock still pins v1's commit
        self.new_machine()
        self.user_lock.parent.mkdir(parents=True)
        self.user_lock.write_text(text)
        self.frozen()
        self.assertEqual(tree(self.home / ".claude"), first)
        self.assertEqual(self.user_lock.read_text(), text)
        self.assertIn("python-validate for tests.\n---\nBody.",
                      (self.home / ".claude/skills/python-validate/SKILL.md").read_text())

    def move_packs_tag(self) -> None:
        git("tag", "-f", "v1", rev(self.packs_bare, "v2"), cwd=self.packs_bare)

    def test_a_folder_that_differs_from_the_lock_fails(self):
        self.use(python="python")
        self.apply()
        self.use(python="rust")
        out = self.frozen(1)
        self.assertIn("pack python: `subdir` is 'rust' in packs.toml but 'python' in brainrc.lock", out)

    def test_check_passes_on_a_subdir_pack(self):
        self.use(python="python")
        self.apply()
        got, out = quiet(brainrc.cli.cmd_check, None)
        self.assertEqual(got, 0, out)


class SubdirProjectTest(SubdirCase):  # ProjectCase's repo (self.proj) is the current directory
    def test_a_project_pack_from_a_folder(self):
        (self.proj / "brainrc.toml").write_text(
            f'[packs.python]\ngit = "{self.packs_url}"\nref = "v1"\nsubdir = "python"\n')
        self.apply()
        self.assertTrue((self.proj / ".agents/skills/python-validate/SKILL.md").is_file())
        entry = lock.read(self.proj / "brainrc.lock")["packs"]["python"]
        self.assertEqual(entry["subdir"], "python")

    def test_subdir_with_path_is_refused(self):
        (self.proj / "brainrc.toml").write_text('[packs.python]\npath = "packs"\nsubdir = "python"\n')
        out = self.apply(1)
        self.assertIn("brainrc.toml", out)


if __name__ == "__main__":
    import unittest
    unittest.main()
