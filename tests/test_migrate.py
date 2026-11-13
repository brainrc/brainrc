"""Contract tests for `brainrc migrate` (spec 206, AC7-AC13).

Every case runs against a fresh temp HOME with an explicit env, never the real home.
"""
import contextlib
import errno
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
from brainrc import cli  # noqa: E402
from support import bare_env, home_env, readlink, symlink  # noqa: E402
from test_brainrc import default_pack_env  # noqa: E402

HOME_VARS = ("HOME", "USERPROFILE", "BRAINRC_HOME", "AICFG_HOME", "XDG_CONFIG_HOME", "CLAUDE_CONFIG_DIR", "CODEX_HOME", "PYTHONWARNINGS")
LOCAL_FILES = {
    "packs.local.toml": "# no packs\n",
    "harnesses.local.toml": "# no overrides\n",
    "rules/90-mine.local.md": "trigger: always_on\nmine\n",
}


class MigrateCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        (self.home / ".claude").mkdir()  # an installed harness, so apply links into it (#126)
        self.new = self.home / ".config" / "brainrc"
        self.old = self.home / ".config" / "ai-config"

    def run_cli(self, *args, **env_vars):
        env = {k: v for k, v in os.environ.items() if k not in HOME_VARS}
        env.update(default_pack_env())  # the default pack comes from a local stand-in, not GitHub
        env.update(home_env(self.home))
        env.update(env_vars)
        return subprocess.run([sys.executable, "scripts/brainrc.py", *args], cwd=REPO, env=env,
                              capture_output=True, text=True, timeout=120)

    def legacy_install(self):
        """An old dir with local files, then an apply that links into it."""
        for rel, text in LOCAL_FILES.items():
            (self.old / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.old / rel).write_text(text)
        proc = self.run_cli("apply", BRAINRC_HOME=str(self.old))  # 0.5.0 no longer reads the old dir
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def links_into(self, directory):
        found = []
        for base, dirs, files in os.walk(self.home):
            for name in dirs + files:
                p = Path(base, name)
                if p.is_symlink() and readlink(p).startswith(str(directory)):
                    found.append(p)
        return found

    def snapshot(self):
        return sorted(p.relative_to(self.tmp).as_posix() for p in self.tmp.rglob("*"))


class TestMigrate(MigrateCase):
    def test_ac7_moves_old_dir_and_repoints_links(self):
        self.legacy_install()
        self.assertTrue(self.links_into(self.old))
        proc = self.run_cli("migrate")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(self.old.exists())
        for rel, text in LOCAL_FILES.items():
            self.assertEqual((self.new / rel).read_text(), text)
        self.assertEqual(self.links_into(self.old), [])
        self.assertTrue(self.links_into(self.new))
        self.assertNotIn("deprecated", proc.stderr)
        self.assertNotIn("CONFLICT", proc.stdout)

    def test_ac7_symlinked_old_dir_moves_as_the_link(self):
        real = self.tmp / "real"
        real.mkdir()
        (real / "packs.local.toml").write_text("# x\n")
        self.old.parent.mkdir(parents=True)
        symlink(self.old, real)
        proc = self.run_cli("migrate")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(self.new.is_symlink())
        self.assertEqual(readlink(self.new), str(real))
        self.assertTrue((real / "packs.local.toml").is_file())
        self.assertFalse(os.path.lexists(self.old))

    def test_ac7_relative_symlinked_old_dir_into_empty_target_moves_as_the_link(self):
        real = self.home / "dotfiles" / "brainrc-settings"
        real.mkdir(parents=True)
        (real / "packs.local.toml").write_text("# x\n")
        self.old.parent.mkdir(parents=True)
        symlink(self.old, Path("..") / "dotfiles" / "brainrc-settings")
        brainrc_home = self.home / "elsewhere" / "brainrc"
        brainrc_home.mkdir(parents=True)  # an existing empty target (AC8)
        proc = self.run_cli("migrate", BRAINRC_HOME=str(brainrc_home))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(brainrc_home.is_symlink())
        self.assertEqual(brainrc_home.resolve(), real.resolve())
        self.assertFalse(os.path.lexists(self.old))

    def test_ac8_non_empty_target_refused(self):
        self.legacy_install()
        self.new.mkdir(parents=True)
        (self.new / "keep.txt").write_text("keep")
        before = self.snapshot()
        proc = self.run_cli("migrate")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ai-config", proc.stdout + proc.stderr)
        self.assertIn("brainrc", proc.stdout + proc.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_ac8_empty_target_accepted(self):
        self.legacy_install()
        self.new.mkdir(parents=True)
        proc = self.run_cli("migrate")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(self.old.exists())
        self.assertTrue((self.new / "packs.local.toml").is_file())

    def test_ac9_dry_run_writes_nothing(self):
        self.legacy_install()
        before = self.snapshot()
        proc = self.run_cli("migrate", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(self.old.as_posix().replace(self.home.as_posix(), "~"), proc.stdout)
        self.assertIn("~/.config/brainrc", proc.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_ac9_dry_run_non_empty_target_fails(self):
        self.old.mkdir(parents=True)
        self.new.mkdir(parents=True)
        (self.new / "keep.txt").write_text("keep")
        proc = self.run_cli("migrate", "--dry-run")
        self.assertNotEqual(proc.returncode, 0)

    def test_ac10_nothing_to_migrate_is_idempotent(self):
        proc = self.run_cli("migrate")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("nothing to migrate", proc.stdout.lower())
        self.assertEqual(self.snapshot(), ["home", "home/.claude"])
        self.legacy_install()
        self.assertEqual(self.run_cli("migrate").returncode, 0)
        before = self.snapshot()
        again = self.run_cli("migrate")
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertIn("nothing to migrate", again.stdout.lower())
        self.assertEqual(self.snapshot(), before)

    def test_ac11_aicfg_home_without_brainrc_home_refused(self):
        src = self.tmp / "src"
        src.mkdir()
        (src / "packs.local.toml").write_text("# x\n")
        before = self.snapshot()
        proc = self.run_cli("migrate", AICFG_HOME=str(src))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("BRAINRC_HOME", proc.stdout + proc.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_ac11_aicfg_home_is_source_when_brainrc_home_set(self):
        src, dst = self.tmp / "src", self.tmp / "dst"
        src.mkdir()
        (src / "packs.local.toml").write_text("# x\n")
        proc = self.run_cli("migrate", AICFG_HOME=str(src), BRAINRC_HOME=str(dst))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(src.exists())
        self.assertTrue((dst / "packs.local.toml").is_file())

    def test_ac12_held_lock_blocks_move(self):
        self.old.mkdir(parents=True)
        with open(self.old / "apply.lock", "a") as f:
            self.assertTrue(cli._try_lock(f))  # flock or msvcrt, as apply takes it
            proc = self.run_cli("migrate")
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(self.old.is_dir())
        self.assertFalse(self.new.exists())

    def test_ac13_failing_apply_reports_move_done(self):
        self.old.mkdir(parents=True)
        (self.old / "packs.local.toml").write_text("# no packs\n")
        (self.home / ".claude" / "CLAUDE.md").write_text("mine")  # a CONFLICT makes apply exit 1
        proc = self.run_cli("migrate")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(self.old.exists())
        self.assertTrue(self.new.is_dir())
        out = proc.stdout + proc.stderr
        self.assertIn("the move is done", out)
        self.assertIn("apply`", out)  # `brainrc apply`, or the script form in a checkout


class TestCrossDevice(MigrateCase):
    def test_exdev_falls_back_to_copy_then_removes_source(self):
        from brainrc import cli, migrate
        self.legacy_install()
        real_rename = os.rename

        def rename(src, dst, *a, **kw):
            if str(src) == str(self.old):
                raise OSError(errno.EXDEV, "cross-device")
            return real_rename(src, dst, *a, **kw)

        env = bare_env(self.home)
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch("os.rename", side_effect=rename), \
                mock.patch.object(cli, "cmd_sync", return_value=0):
            self.assertEqual(migrate.cmd_migrate(dry_run=False), 0)
        self.assertFalse(self.old.exists())
        for rel, text in LOCAL_FILES.items():
            self.assertEqual((self.new / rel).read_text(), text)
        self.assertEqual([p.name for p in self.new.parent.iterdir() if "tmp" in p.name], [])


def exdev_rename(old):
    """An os.rename that fails with EXDEV for the given source dir."""
    real = os.rename

    def rename(src, dst, *a, **kw):
        if str(src) == str(old):
            raise OSError(errno.EXDEV, "cross-device")
        return real(src, dst, *a, **kw)
    return rename


class TestCrossDeviceSafety(MigrateCase):
    def migrate_in_process(self, rename, sync=0, **env_vars):
        from brainrc import cli, migrate
        env = bare_env(self.home, **env_vars)
        out = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), mock.patch("os.rename", side_effect=rename), \
                mock.patch.object(cli, "cmd_sync", return_value=sync) as synced, \
                contextlib.redirect_stdout(out):
            code = migrate.cmd_migrate(dry_run=False)
        return code, out.getvalue(), synced

    def test_symlinked_source_moves_as_a_link_across_devices(self):
        real = self.tmp / "real"
        real.mkdir()
        (real / "packs.local.toml").write_text("# x\n")
        self.old.parent.mkdir(parents=True)
        symlink(self.old, real)
        code, out, _ = self.migrate_in_process(exdev_rename(self.old))
        self.assertEqual(code, 0, out)
        self.assertTrue(self.new.is_symlink())
        self.assertEqual(readlink(self.new), str(real))
        self.assertFalse(os.path.lexists(self.old))
        self.assertEqual(sorted(os.listdir(real)), ["apply.lock", "packs.local.toml"])

    def test_relative_symlink_source_still_resolves_after_move(self):
        real = self.old.parent / "real"
        real.mkdir(parents=True)
        (real / "packs.local.toml").write_text("# x\n")
        symlink(self.old, "real")
        code, out, _ = self.migrate_in_process(exdev_rename(self.old))
        self.assertEqual(code, 0, out)
        self.assertTrue(self.new.is_symlink())
        self.assertEqual(self.new.resolve(), real.resolve())

    def test_failed_copy_removes_temp_and_keeps_source(self):
        self.legacy_install()
        before = self.snapshot()
        with mock.patch("shutil.copytree", side_effect=OSError(errno.ENOSPC, "no space")):
            code, out, synced = self.migrate_in_process(exdev_rename(self.old))
        self.assertEqual(code, 1)
        self.assertIn("Nothing moved", out)
        self.assertIn("no space", out)
        self.assertEqual(self.snapshot(), before)
        synced.assert_not_called()

    def test_any_oserror_before_target_in_place_is_reported(self):
        self.legacy_install()
        before = self.snapshot()

        def rename(src, dst, *a, **kw):
            raise OSError(errno.ENOTEMPTY, "Directory not empty")
        code, out, _ = self.migrate_in_process(rename)
        self.assertEqual(code, 1)
        self.assertIn("Nothing moved", out)
        self.assertEqual(self.snapshot(), before)

    @unittest.skipIf(os.name == "nt", "Windows has no Unix mode bits to copy")
    def test_temp_dir_has_the_source_mode(self):
        self.legacy_install()
        os.chmod(self.old, 0o700)
        modes = []
        real = tempfile.mkdtemp

        def mkdtemp(*a, **kw):
            d = real(*a, **kw)
            modes.append(os.stat(d).st_mode & 0o777)
            return d
        with mock.patch("tempfile.mkdtemp", side_effect=mkdtemp), \
                mock.patch("shutil.copytree", side_effect=OSError(errno.EIO, "stop")) as copy:
            self.migrate_in_process(exdev_rename(self.old))
        self.assertTrue(copy.called)
        self.assertEqual(modes, [0o700])  # chmod happens after mkdtemp's own 0700; never wider

    def test_source_that_cannot_be_removed_still_applies_and_fails(self):
        self.legacy_install()
        old = self.old

        def rmtree(path, *a, **kw):
            if str(path) == str(old):
                raise OSError(errno.EACCES, "denied")
        with mock.patch("shutil.rmtree", side_effect=rmtree):
            code, out, synced = self.migrate_in_process(exdev_rename(self.old))
        self.assertEqual(code, 1)
        self.assertIn("the copy is in place", out)
        self.assertIn("could not be fully removed", out)
        self.assertIn(old.as_posix().replace(self.home.as_posix(), "~"), out)
        self.assertIn("denied", out)
        self.assertTrue((self.new / "packs.local.toml").is_file())
        synced.assert_called_once()


class TestPathSanity(MigrateCase):
    def refused(self, needle, **env_vars):
        before = self.snapshot()
        proc = self.run_cli("migrate", **env_vars)
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Nothing moved", proc.stdout)
        self.assertIn(needle, proc.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_relative_env_value_refused(self):
        (self.tmp / "rel").mkdir()
        self.refused("relative", AICFG_HOME="rel", BRAINRC_HOME=str(self.tmp / "dst"))
        self.refused("relative", BRAINRC_HOME="dst")

    def test_home_dir_as_source_refused(self):
        (self.home / "packs").mkdir()
        self.refused("home directory", AICFG_HOME=str(self.home), BRAINRC_HOME=str(self.tmp / "dst"))

    def test_root_as_source_refused(self):
        self.refused("home directory", AICFG_HOME=self.tmp.anchor,  # "/", or "C:\\" on Windows
                     BRAINRC_HOME=str(self.tmp / "dst"))

    def test_ancestor_of_target_refused(self):
        src = self.tmp / "src"
        (src / "rules").mkdir(parents=True)
        self.refused("inside", AICFG_HOME=str(src), BRAINRC_HOME=str(src / "new"))

    def test_source_that_is_a_file_refused(self):
        src = self.tmp / "src"
        src.write_text("x")
        self.refused("not a directory", AICFG_HOME=str(src), BRAINRC_HOME=str(self.tmp / "dst"))

    def test_dir_that_is_not_a_settings_home_refused(self):
        src = self.tmp / "src"
        src.mkdir()
        (src / "notes.txt").write_text("x")
        self.refused("settings home", AICFG_HOME=str(src), BRAINRC_HOME=str(self.tmp / "dst"))

    def test_parent_of_home_as_source_refused(self):
        (self.tmp / "packs.local.toml").write_text("# x\n")
        self.refused("above it", AICFG_HOME=str(self.tmp), BRAINRC_HOME=str(self.tmp / "dst"))

    def test_dir_with_only_generic_names_refused(self):
        src = self.tmp / "src"
        for name in ("rules", "hooks", "packs"):
            (src / name).mkdir(parents=True)
        self.refused("settings home", AICFG_HOME=str(src), BRAINRC_HOME=str(self.tmp / "dst"))

    def test_dir_with_only_local_rules_is_a_settings_home(self):
        src = self.tmp / "src"
        (src / "rules").mkdir(parents=True)
        (src / "rules" / "90-mine.local.md").write_text("trigger: always_on\nmine\n")
        proc = self.run_cli("migrate", "--dry-run", AICFG_HOME=str(src), BRAINRC_HOME=str(self.tmp / "dst"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_target_symlink_is_not_replaced(self):
        self.legacy_install()
        self.new.parent.mkdir(parents=True, exist_ok=True)
        empty = self.tmp / "empty"
        empty.mkdir()
        symlink(self.new, empty)
        before = self.snapshot()
        proc = self.run_cli("migrate")
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.snapshot(), before)


class TestLocks(MigrateCase):
    def test_lock_of_the_resolved_home_blocks_when_both_env_vars_set(self):
        src, dst = self.tmp / "src", self.tmp / "dst"
        src.mkdir()
        (src / "packs.local.toml").write_text("# x\n")
        dst.mkdir()
        with open(dst / "apply.lock", "a") as f:  # what a running apply holds with BRAINRC_HOME set
            self.assertTrue(cli._try_lock(f))
            proc = self.run_cli("migrate", AICFG_HOME=str(src), BRAINRC_HOME=str(dst))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("another brainrc apply", proc.stdout)
        self.assertTrue((src / "packs.local.toml").is_file())
        self.assertEqual(sorted(p.name for p in dst.iterdir()), ["apply.lock"])

    def test_dry_run_creates_no_lock_files(self):
        self.old.mkdir(parents=True)
        (self.old / "packs.local.toml").write_text("# x\n")
        before = self.snapshot()
        self.assertEqual(self.run_cli("migrate", "--dry-run").returncode, 0)
        self.assertEqual(self.snapshot(), before)


class TestLinkRepoint(unittest.TestCase):
    def state(self, home, link_to, desired_rel="rules/x.md"):
        from brainrc import plan
        tmp = Path(home)
        new, old = tmp / ".config" / "brainrc", tmp / ".config" / "ai-config"
        old.mkdir(parents=True)
        new.mkdir(parents=True)
        dest = tmp / "dest"
        symlink(dest, old / link_to)
        env = bare_env(tmp)
        with mock.patch.dict(os.environ, env, clear=True):
            return plan.Link("claude", dest, new / desired_rel).state()

    def test_link_apply_made_from_the_old_home_is_repointed(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.state(d, "rules/x.md"), "update")

    def test_other_link_into_the_old_home_stays_a_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.state(d, "notes/mine.md"), "conflict")


if __name__ == "__main__":
    unittest.main()
