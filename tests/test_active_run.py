"""Tests for skills/spec-agent/scripts/active_run.py: write and read the active-run pointer that
external tools use to locate the current spec-agent run."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills/spec-agent/scripts/active_run.py"


class ActiveRunTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.home = self.root / "home"
        self.home.mkdir()
        self.aicfg = self.root / "cfg" / "ai-config"  # parent does not exist yet
        self.repo_a = self.root / "repo-a"
        self.cwd_b = self.root / "elsewhere"
        self.cwd_b.mkdir()

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_dir(self, slug: str, base: Path | None = None, mtime: float | None = None) -> Path:
        run = (base or self.repo_a) / "specs" / slug
        run.mkdir(parents=True, exist_ok=True)
        state = run / "state.json"
        state.write_text("{}")
        if mtime is not None:
            os.utime(state, (mtime, mtime))
        return run

    def env(self, aicfg_home: Path | str | None = "default") -> dict:
        env = {k: v for k, v in os.environ.items() if k != "AICFG_HOME"}
        env["HOME"] = str(self.home)
        if aicfg_home == "default":
            aicfg_home = self.aicfg
        if aicfg_home is not None:
            env["AICFG_HOME"] = str(aicfg_home)
        return env

    def cli(self, *args, cwd=None, aicfg_home="default"):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True, text=True, cwd=cwd or self.cwd_b, env=self.env(aicfg_home),
        )

    @property
    def pointer(self) -> Path:
        return self.aicfg / "active-run"

    # AC1, AC8
    def test_write_from_other_directory_records_absolute_run_path(self):
        run = self.run_dir("071-x")
        result = self.cli("write", str(run), cwd=self.cwd_b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pointer.read_text(), f"{run}\n")

    def test_write_resolves_relative_run_dir_to_absolute(self):
        run = self.run_dir("071-x")
        result = self.cli("write", "specs/071-x", cwd=self.repo_a)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pointer.read_text(), f"{run}\n")

    # AC2
    def test_write_defaults_to_dot_config_ai_config_when_env_unset(self):
        run = self.run_dir("071-x")
        result = self.cli("write", str(run), aicfg_home=None)
        self.assertEqual(result.returncode, 0, result.stderr)
        default = self.home / ".config/ai-config/active-run"
        self.assertEqual(default.read_text(), f"{run}\n")

    # AC3
    def test_pointer_is_single_line_path_plus_newline_only(self):
        run = self.run_dir("071-x")
        self.cli("write", str(run))
        self.assertEqual(self.pointer.read_bytes(), f"{run}\n".encode())

    # AC5
    def test_write_replaces_another_runs_pointer(self):
        first = self.run_dir("070-a-much-longer-run-slug-than-the-next-one")
        second = self.run_dir("071-new")
        self.cli("write", str(first))
        self.cli("write", str(second))
        self.assertEqual(self.pointer.read_text(), f"{second}\n")

    def test_write_same_run_twice_is_idempotent(self):
        run = self.run_dir("071-x")
        self.cli("write", str(run))
        self.cli("write", str(run))
        self.assertEqual(self.pointer.read_text(), f"{run}\n")

    # AC8
    def test_write_creates_missing_aicfg_home_directory(self):
        run = self.run_dir("071-x")
        self.assertFalse(self.aicfg.exists())
        result = self.cli("write", str(run))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.aicfg.is_dir())
        self.assertTrue(self.pointer.is_file())

    # AC9
    def test_read_prints_pointer_run_when_directory_exists(self):
        run = self.run_dir("071-x")
        self.cli("write", str(run))
        result = self.cli("read", cwd=self.cwd_b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(run))

    def test_read_prefers_pointer_over_newer_run_in_cwd(self):
        pointed = self.run_dir("070-pointed", mtime=1_000_000)
        self.run_dir("071-newer", base=self.cwd_b, mtime=2_000_000)
        self.cli("write", str(pointed))
        result = self.cli("read", cwd=self.cwd_b)
        self.assertEqual(result.stdout.strip(), str(pointed))

    # AC10
    def test_read_without_pointer_returns_newest_run_in_cwd_specs(self):
        self.run_dir("070-old", base=self.cwd_b, mtime=1_000_000)
        newest = self.run_dir("071-new", base=self.cwd_b, mtime=2_000_000)
        self.run_dir("069-older", base=self.cwd_b, mtime=500_000)
        result = self.cli("read", cwd=self.cwd_b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), newest)

    def test_read_with_pointer_to_missing_directory_falls_back_to_cwd_specs(self):
        newest = self.run_dir("071-new", base=self.cwd_b, mtime=2_000_000)
        self.run_dir("070-old", base=self.cwd_b, mtime=1_000_000)
        self.aicfg.mkdir(parents=True)
        self.pointer.write_text(f"{self.root}/gone/specs/nope\n")
        result = self.cli("read", cwd=self.cwd_b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), newest)

    def test_read_fallback_orders_by_state_json_mtime_not_name(self):
        newest = self.run_dir("aaa-first-by-name", base=self.cwd_b, mtime=2_000_000)
        self.run_dir("zzz-last-by-name", base=self.cwd_b, mtime=1_000_000)
        result = self.cli("read", cwd=self.cwd_b)
        self.assertEqual(Path(result.stdout.strip()).resolve(), newest)

    def test_read_with_nothing_found_prints_nothing_on_stdout(self):
        result = self.cli("read", cwd=self.cwd_b)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.returncode, 1)
        self.assertNotEqual(result.stderr.strip(), "")

    def test_read_with_blank_pointer_falls_back_to_cwd_specs(self):
        newest = self.run_dir("071-new", base=self.cwd_b, mtime=2_000_000)
        self.run_dir("070-old", base=self.cwd_b, mtime=1_000_000)
        self.aicfg.mkdir(parents=True)
        for content in ("\n", "  \n"):
            self.pointer.write_text(content)
            result = self.cli("read", cwd=self.cwd_b)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Path(result.stdout.strip()).resolve(), newest)

    def test_read_with_pointer_naming_a_file_falls_back_to_cwd_specs(self):
        newest = self.run_dir("071-new", base=self.cwd_b, mtime=2_000_000)
        a_file = self.root / "plain.txt"
        a_file.write_text("x")
        self.aicfg.mkdir(parents=True)
        self.pointer.write_text(f"{a_file}\n")
        result = self.cli("read", cwd=self.cwd_b)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), newest)

    # AC11
    def test_write_warns_and_exits_zero_when_aicfg_home_is_a_file(self):
        run = self.run_dir("071-x")
        bad = self.root / "not-a-dir"
        bad.write_text("x")
        result = self.cli("write", str(run), aicfg_home=bad / "sub")
        self.assertEqual(result.returncode, 0)
        self.assertIn("WARN", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_write_warns_and_exits_zero_when_default_home_is_unwritable(self):
        run = self.run_dir("071-x")
        # HOME is a file, so ~/.config/ai-config can never be created (works even as root).
        self.home.rmdir()
        self.home.write_text("x")
        result = self.cli("write", str(run), aicfg_home=None)
        self.assertEqual(result.returncode, 0)
        self.assertIn("WARN", result.stderr)


if __name__ == "__main__":
    unittest.main()
