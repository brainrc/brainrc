"""Copy mode (#177): with link_mode = "copy" (or BRAINRC_LINK_MODE=copy), apply copies each item it
would link and records the copy, and status, doctor and uninstall treat the copies as managed.
Runs the same on every OS: a Windows machine without symlinks takes this path in "auto"."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import home_env, restore_home, rmtree, saved_home  # noqa: E402
from test_brainrc import TempRepoCase, brainrc, install_harnesses, quiet  # noqa: E402

from brainrc import copies  # noqa: E402
from brainrc.sources import tree_files  # noqa: E402
from brainrc.config import ConfigError  # noqa: E402


def links_under(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_symlink()]


class CopyModeTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        self.old_mode = os.environ.get(copies.ENV)
        os.environ[copies.ENV] = "copy"

    def tearDown(self):
        if self.old_mode is None:
            os.environ.pop(copies.ENV, None)
        else:
            os.environ[copies.ENV] = self.old_mode
        restore_home(self.old_home)
        rmtree(self.home)
        super().tearDown()

    def apply(self) -> str:
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        return out

    def status(self) -> tuple[int, str]:
        return quiet(brainrc.cmd_sync, False)

    def a_copy(self, suffix: str) -> Path:
        """A recorded copy of a file (not a directory) whose dest ends with suffix."""
        for dest in copies.read():
            if dest.replace("\\", "/").endswith(suffix):
                return Path(dest)
        self.fail(f"no copy of {suffix} in {sorted(copies.read())}")

    def test_apply_copies_every_item_and_is_in_sync_after(self):
        self.apply()
        self.assertEqual(links_under(self.home), [])
        record = copies.read()
        self.assertTrue(record)
        for dest, entry in record.items():
            # Each file is its source's bytes, but for the line that finds the file's own path.
            dest, source = Path(dest), Path(entry["source"])
            pairs = [(dest / r, source / r) for r, _ in tree_files(source)] if source.is_dir() else [(dest, source)]
            self.assertTrue(pairs, dest)
            for got, src in pairs:
                want = brainrc.adapters.get(entry["harness"]).copied_file(src.read_text(encoding="utf-8"), src)
                self.assertEqual(got.read_text(encoding="utf-8"), want, got)
        self.assertEqual(self.status(), (0, "Everything in sync.\n"))
        self.assertEqual(self.apply().strip(), "Everything in sync.")

    def test_a_changed_source_shows_as_an_update_and_apply_refreshes_the_copy(self):
        self.apply()
        dest = self.a_copy("/.claude/agents/code-reviewer.md")
        source = Path(copies.recorded(dest)["source"])
        source.write_text(source.read_text() + "\nOne more line.\n")
        code, out = self.status()
        self.assertIn("UPDATE", out)
        self.assertIn("code-reviewer.md", out)
        self.apply()
        self.assertEqual(dest.read_text(), source.read_text())
        self.assertEqual(self.status(), (0, "Everything in sync.\n"))

    def test_an_edited_copy_is_reported_and_left_alone(self):
        self.apply()
        dest = self.a_copy("/.claude/agents/code-reviewer.md")
        dest.write_text("My own notes.\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("EDITED", out)
        self.assertIn("1 copy edited since apply wrote it", out)
        self.assertEqual(dest.read_text(), "My own notes.\n")
        findings = [f for f in brainrc.doctor_findings() if "code-reviewer.md" in f[1]]
        self.assertEqual([f[0] for f in findings], ["FAIL"], findings)
        self.assertIn("edited since apply wrote it", findings[0][1])

    def test_a_skill_dropped_from_the_sources_is_pruned(self):
        self.apply()
        skill = next(Path(d) for d in copies.read() if Path(d).parent.name == "skills" and Path(d).is_dir())
        source = Path(copies.recorded(skill)["source"])
        shutil.rmtree(source)
        self.apply()
        self.assertFalse(os.path.lexists(skill))
        self.assertNotIn(copies.key(skill), copies.read())

    def test_switching_modes_replaces_links_with_copies_and_back(self):
        os.environ[copies.ENV] = "symlink"
        self.apply()
        self.assertTrue(links_under(self.home))
        self.assertFalse(copies.record_path().exists())
        os.environ[copies.ENV] = "copy"
        self.assertIn("UPDATE", self.status()[1])
        self.apply()
        self.assertEqual(links_under(self.home), [])
        self.assertEqual(self.status(), (0, "Everything in sync.\n"))
        os.environ[copies.ENV] = "symlink"
        self.apply()
        self.assertTrue(links_under(self.home))
        self.assertFalse(copies.record_path().exists())
        self.assertEqual(self.status(), (0, "Everything in sync.\n"))

    def test_uninstall_removes_the_copies_and_keeps_an_edited_one_as_a_backup(self):
        self.apply()
        edited = self.a_copy("/.claude/agents/code-reviewer.md")
        edited.write_text("My own notes.\n")
        code, out = quiet(brainrc.uninstall.cmd_uninstall)
        self.assertEqual(code, 0, out)
        self.assertIn("SETASIDE", out)
        self.assertFalse(copies.record_path().exists())
        left = [p for p in self.home.rglob("*") if not p.is_dir()]
        self.assertEqual([p.name for p in left if ".bak-brainrc-" not in p.name], [], left)
        backups = list(edited.parent.glob("code-reviewer.md.bak-brainrc-*"))
        self.assertEqual([b.read_text() for b in backups], ["My own notes.\n"])

    def test_opencode_plugin_copy_finds_the_hooks_from_its_source(self):
        self.apply()
        dest = self.a_copy("/opencode/plugins/brainrc-guard.js")
        source = Path(copies.recorded(dest)["source"])
        text = dest.read_text()
        self.assertNotIn("realpathSync(fileURLToPath(import.meta.url))", text)
        self.assertIn(json.dumps(str(source)), text)
        self.assertEqual(text.replace(json.dumps(str(source)), "realpathSync(fileURLToPath(import.meta.url))"),
                         source.read_text())

    def test_a_copied_hook_still_finds_the_guards(self):
        """Codex's guard.py imports Claude Code's guards from beside its own real path. A copy is
        told its source's path, so it denies what the linked hook denies."""
        self.apply()
        hooks = self.a_copy("/.codex/hooks/brainrc")
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": str(self.home),
                   "tool_input": {"command": "git push origin main"}, "session_id": "s"}
        result = subprocess.run([sys.executable, str(hooks / "guard.py")], input=json.dumps(payload),
                                capture_output=True, text=True, timeout=30, cwd=self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.status(), (0, "Everything in sync.\n"))  # a run's __pycache__ doesn't count

    def test_a_dangling_link_in_a_skill_is_left_out_and_a_relative_one_followed(self):
        if not copies.can_symlink():
            self.skipTest("this machine can't make the links the test copies")
        skill = self.repo / "skills/acme-links"
        (skill / "more").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: acme-links\ndescription: Links. Use for tests.\n---\nHi.\n")
        (skill / "more/notes.md").write_text("Notes.\n")
        os.symlink("more", skill / "alias", target_is_directory=True)
        os.symlink("gone.md", skill / "dangling.md")
        dest = self.place_one(skill)
        self.assertEqual(sorted(r for r, _ in tree_files(dest)), ["SKILL.md", "alias/notes.md", "more/notes.md"])
        self.assertFalse(os.path.lexists(dest / "dangling.md"))

    def place_one(self, source: Path) -> Path:
        dest = self.home / "copied" / source.name
        dest.parent.mkdir()
        copies.place("claude", dest, source)
        return dest

    def test_a_failed_copy_leaves_what_was_there(self):
        self.apply()
        dest = self.a_copy("/.claude/agents/code-reviewer.md")
        before = dest.read_text()
        with unittest.mock.patch("shutil.copyfile", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                copies.place("claude", dest, Path(copies.recorded(dest)["source"]))
        self.assertEqual(dest.read_text(), before)
        self.assertEqual([p.name for p in dest.parent.iterdir() if "brainrc-tmp" in p.name], [])

    def test_uninstall_restores_the_instructions_file_init_moved_aside(self):
        self.apply()
        dest = self.a_copy("/.claude/CLAUDE.md")
        backup = dest.with_name("CLAUDE.md.bak-brainrc-20260101T000000Z")
        backup.write_text("My own CLAUDE.md.\n")
        code, out = quiet(brainrc.uninstall.cmd_uninstall)
        self.assertEqual(code, 0, out)
        self.assertEqual(dest.read_text(), "My own CLAUDE.md.\n")

    def test_init_does_not_adopt_a_copied_instructions_file(self):
        self.apply()
        names = list(brainrc.config.load_harnesses())
        roots = [self.repo]
        found = [p for _, p in brainrc.init._instruction_files(names, roots)]
        self.assertEqual(found, [])


class LinkModeConfigTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.old_mode = os.environ.pop(copies.ENV, None)

    def tearDown(self):
        if self.old_mode is not None:
            os.environ[copies.ENV] = self.old_mode
        super().tearDown()

    def test_default_is_auto_and_auto_links_where_links_work(self):
        self.assertEqual(copies.configured(), "auto")
        self.assertEqual(copies.mode(), "symlink" if copies.can_symlink() else "copy")

    def test_the_file_sets_the_mode_and_the_variable_overrides_it(self):
        (brainrc.config.local_dir() / "brainrc.local.toml").write_text('link_mode = "copy"\n')
        self.assertTrue(copies.copying())
        os.environ[copies.ENV] = "symlink"
        self.addCleanup(os.environ.pop, copies.ENV, None)
        self.assertFalse(copies.copying())

    def test_an_unknown_mode_is_a_config_error_naming_the_line(self):
        path = brainrc.config.local_dir() / "brainrc.local.toml"
        path.write_text('profile = "full"\nlink_mode = "hardlink"\n')
        with self.assertRaisesRegex(ConfigError, r"brainrc\.local\.toml:2: `link_mode` must be one of"):
            copies.configured()
        path.unlink()
        os.environ[copies.ENV] = "junction"
        self.addCleanup(os.environ.pop, copies.ENV, None)
        with self.assertRaisesRegex(ConfigError, "BRAINRC_LINK_MODE='junction'"):
            copies.configured()


if __name__ == "__main__":
    unittest.main()
