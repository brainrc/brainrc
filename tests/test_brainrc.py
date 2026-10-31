"""Tests for scripts/brainrc.py: settings merge, sync against a fake HOME, and validation."""
import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import brainrc  # noqa: E402  (the package at the repo root)

FOREIGN = {"hooks": [{"type": "command", "command": "node /opt/other/hook.js"}]}
OURS_OLD = {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/ai-config/old.py"}]}
SOURCES = ("skills", "agents", "overrides", "rules")  # core ships no commands/ (packs may)
FRAGMENT = REPO / "overrides/claude/settings.fragment.json"


def claude_guard(hooks_dir: str, script: str) -> str:
    """A Claude Code hook command as the fragment renders it: skipped when the script is gone."""
    return f'f="{hooks_dir}/{script}"; [ ! -f "$f" ] || python3 "$f"'


def cursor_guard(hooks_dir: str) -> str:
    """A Cursor hook command as the fragment renders it: allows when the guard is gone."""
    return f'f="{hooks_dir}/guard.py"; if [ -f "$f" ]; then python3 "$f"; else echo \'{{"permission": "allow"}}\'; fi'


def quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*args)
    return code, buf.getvalue()


def copy_repo(dest: Path) -> None:
    """Sources plus the committed harnesses.toml only: never the developer's *.local.* files."""
    for name in SOURCES:
        shutil.copytree(REPO / name, dest / name, symlinks=True,
                        ignore=shutil.ignore_patterns("*.local.md", "__pycache__"))
    shutil.copy2(REPO / "harnesses.toml", dest / "harnesses.toml")
    shutil.copy2(REPO / "VERSION", dest / "VERSION")
    shutil.copy2(REPO / "CHANGELOG.md", dest / "CHANGELOG.md")


def set_core_version(repo: Path, version: str) -> None:
    """VERSION plus a CHANGELOG whose newest entry matches, as validate requires."""
    (repo / "VERSION").write_text(version + "\n")
    (repo / "CHANGELOG.md").write_text(f"# Changelog\n\n## {version} (2026-01-01)\n\n- Change.\n")


class TempRepoCase(unittest.TestCase):
    """Point brainrc at a throwaway copy of the repo and BRAINRC_HOME, so tests never read local
    config or write rendered files anywhere real."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        copy_repo(self.repo)
        self.old_repo = brainrc.config.REPO
        brainrc.config.REPO = self.repo
        self.settings_home = Path(tempfile.mkdtemp()) / "brainrc"
        self.old_brainrc_home = os.environ.get("BRAINRC_HOME")
        os.environ["BRAINRC_HOME"] = str(self.settings_home)
        self.old_xdg = os.environ.pop("XDG_CONFIG_HOME", None)  # CI runners set it

    def tearDown(self):
        brainrc.config.REPO = self.old_repo
        if self.old_brainrc_home is None:
            os.environ.pop("BRAINRC_HOME", None)
        else:
            os.environ["BRAINRC_HOME"] = self.old_brainrc_home
        if self.old_xdg is not None:
            os.environ["XDG_CONFIG_HOME"] = self.old_xdg
        shutil.rmtree(self.settings_home.parent)
        shutil.rmtree(self.repo)


class ReleaseTest(TempRepoCase):
    def fragment(self, name: str, bump: str, entry: str) -> None:
        d = self.repo / "changelog.d"
        d.mkdir(exist_ok=True)
        (d / name).write_text(f"---\nbump: {bump}\n---\n{entry}\n")

    def test_next_version(self):
        self.assertEqual(brainrc.next_version((0, 3, 9), "patch"), (0, 3, 10))
        self.assertEqual(brainrc.next_version((0, 3, 9), "minor"), (0, 4, 0))
        self.assertEqual(brainrc.next_version((0, 3, 9), "major"), (1, 0, 0))

    def test_release_takes_the_largest_bump_and_removes_fragments(self):
        set_core_version(self.repo, "0.3.9")
        (self.repo / "changelog.d").mkdir()
        (self.repo / "changelog.d/README.md").write_text("How to write a fragment.\n")
        self.fragment("a-fix.md", "patch", "- Fixed a thing.")
        self.fragment("b-contract.md", "minor", "- **[pack contract]** New key.")
        code, out = quiet(brainrc.cmd_release)
        self.assertEqual(code, 0, out)
        self.assertEqual((self.repo / "VERSION").read_text(), "0.4.0\n")
        changelog = (self.repo / "CHANGELOG.md").read_text()
        self.assertRegex(changelog, r"## 0\.4\.0 \(\d{4}-\d\d-\d\d\)\n\n- Fixed a thing\.\n- \*\*\[pack contract\]")
        self.assertLess(changelog.index("## 0.4.0"), changelog.index("## 0.3.9"))
        self.assertEqual([p.name for p in (self.repo / "changelog.d").iterdir()], ["README.md"])
        from brainrc.sources import check_changelog, core_version
        self.assertEqual(check_changelog(core_version()), [])

    def test_dry_run_and_no_fragments_write_nothing(self):
        set_core_version(self.repo, "0.3.9")
        code, out = quiet(brainrc.cmd_release)
        self.assertIn("nothing to release", out)
        self.fragment("a.md", "patch", "- Fixed.")
        code, out = quiet(brainrc.cmd_release, True)
        self.assertIn("Would release 0.3.10", out)
        self.assertEqual((self.repo / "VERSION").read_text(), "0.3.9\n")
        self.assertTrue((self.repo / "changelog.d/a.md").is_file())

    def test_notes_print_one_versions_section(self):
        (self.repo / "CHANGELOG.md").write_text(
            "# Changelog\n\nIntro.\n\n## 0.3.10 (2026-01-02)\n\n- New.\n- Also new.\n\n"
            "## 0.3.9 (2026-01-01)\n\n- Old.\n")
        self.assertEqual(quiet(brainrc.main, ["brainrc.py", "release", "--notes", "0.3.10"]), (0, "- New.\n- Also new.\n"))
        self.assertEqual(quiet(brainrc.main, ["brainrc.py", "release", "--notes", "0.3.9"]), (0, "- Old.\n"))

    def test_notes_for_a_missing_version_fail(self):
        (self.repo / "CHANGELOG.md").write_text("# Changelog\n\n## 0.3.10 (2026-01-02)\n\n- New.\n")
        code, out = quiet(brainrc.main, ["brainrc.py", "release", "--notes", "0.3.1"])  # not a prefix match
        self.assertEqual(code, 1, out)
        self.assertEqual(out, "ERROR CHANGELOG.md has no section for 0.3.1\n")

    def test_a_bump_into_the_shim_removal_release_fails_while_shims_remain(self):
        set_core_version(self.repo, "0.4.5")
        self.fragment("a.md", "minor", "- Breaking.")
        with mock.patch.object(brainrc.cli, "SHIM_REMOVED_IN", "0.5.0", create=True):
            errors = brainrc.check_fragments()
            self.assertTrue(any("0.5.0" in e and "deprecated" in e for e in errors), errors)
            self.fragment("a.md", "patch", "- Fine.")
            self.assertEqual(brainrc.check_fragments(), [])

    def test_the_removal_check_is_off_once_the_shims_are_gone(self):
        set_core_version(self.repo, "0.4.5")
        self.fragment("a.md", "minor", "- Removes the old names.")
        self.assertFalse(hasattr(brainrc.cli, "SHIM_REMOVED_IN"))  # 0.5.0 removed them
        self.assertEqual(brainrc.check_fragments(), [])

    def test_bad_fragments_fail_validation_and_release(self):
        set_core_version(self.repo, "0.3.9")
        self.fragment("a.md", "huge", "- Fixed.")
        self.fragment("b.md", "patch", "Not a bullet.")
        (self.repo / "changelog.d/c.md").write_text("- No frontmatter.\n")
        errors = brainrc.check_fragments()
        self.assertEqual(len(errors), 3, errors)
        self.assertTrue(any("a.md" in e and "bump" in e for e in errors), errors)
        code, out = quiet(brainrc.cmd_release)
        self.assertEqual(code, 1)
        self.assertEqual((self.repo / "VERSION").read_text(), "0.3.9\n")


class MergeSettingsTest(unittest.TestCase):
    def setUp(self):
        self.fragment = brainrc.render_fragment(FRAGMENT, "~/.claude/hooks/ai-config")

    def test_renders_hooks_dir_placeholder(self):
        commands = [h["command"] for g in self.fragment["hooks"]["PreToolUse"] for h in g["hooks"]]
        self.assertIn(claude_guard("$HOME/.claude/hooks/ai-config", "guard_outward.py"), commands)
        self.assertFalse(any(brainrc.HOOKS_DIR_PLACEHOLDER in c for c in commands))

    def test_custom_hooks_dir_is_owned(self):
        m = brainrc.SettingsMerge("claude", Path("unused"), [(FRAGMENT, "/opt/hooks/mine")])
        once = brainrc.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, m.wanted(), m.markers())
        self.assertEqual(brainrc.merge_settings(once, m.wanted(), m.markers()), once)
        self.assertIn("/opt/hooks/mine/guard_outward.py", json.dumps(once))

    def test_preserves_foreign_hooks_and_other_keys(self):
        current = {"tui": "fullscreen", "hooks": {"SessionStart": [FOREIGN], "PreToolUse": [FOREIGN]}}
        merged = brainrc.merge_settings(current, self.fragment)
        self.assertEqual(merged["tui"], "fullscreen")
        self.assertEqual(merged["hooks"]["SessionStart"], [FOREIGN])
        self.assertEqual(merged["hooks"]["PreToolUse"][0], FOREIGN)
        self.assertEqual(len(merged["hooks"]["PreToolUse"]), 1 + len(self.fragment["hooks"]["PreToolUse"]))

    def test_idempotent(self):
        once = brainrc.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, self.fragment)
        self.assertEqual(brainrc.merge_settings(once, self.fragment), once)

    def test_replaces_stale_owned_groups(self):
        merged = brainrc.merge_settings({"hooks": {"PostToolUse": [OURS_OLD]}}, self.fragment)
        self.assertNotIn("PostToolUse", merged["hooks"])
        self.assertNotIn(OURS_OLD, merged["hooks"]["PreToolUse"])

    def test_does_not_mutate_input(self):
        current = {"hooks": {"PreToolUse": [FOREIGN]}}
        brainrc.merge_settings(current, self.fragment)
        self.assertEqual(current, {"hooks": {"PreToolUse": [FOREIGN]}})


class SyncFakeHomeTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def test_status_writes_nothing(self):
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0)
        self.assertIn("Dry run", out)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse((self.repo / "dist").exists())
        self.assertFalse(self.settings_home.exists())

    def test_relative_symlink_into_repo_is_ok(self):
        quiet(brainrc.cmd_sync, True)
        link = self.home / ".claude/skills/spec-agent"
        link.unlink()
        link.symlink_to(os.path.relpath(self.repo / "skills/spec-agent", link.parent))
        self.assertEqual(brainrc.Link("claude", link, self.repo / "skills/spec-agent").state(), "ok")

    def test_updates_moved_links_and_prunes_dangling(self):
        quiet(brainrc.cmd_sync, True)
        skills_dir = self.home / ".claude/skills"
        (skills_dir / "spec-agent").unlink()
        (skills_dir / "spec-agent").symlink_to(self.repo / "skills/terraform")  # points at wrong skill
        (skills_dir / "gone").symlink_to(self.repo / "skills/gone")  # removed from the repo
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0)
        self.assertIn("UPDATE", out)
        self.assertIn("PRUNE", out)
        self.assertEqual(brainrc.link_target(skills_dir / "spec-agent"), self.repo / "skills/spec-agent")
        self.assertFalse((skills_dir / "gone").is_symlink())

    def test_invalid_settings_json_is_a_conflict(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        settings.write_text("{ not json")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1)
        self.assertIn("invalid JSON", out)
        self.assertEqual(settings.read_text(), "{ not json")

    def test_disabling_harness_removes_only_its_owned_hooks(self):
        quiet(brainrc.cmd_sync, True)
        settings = self.home / ".claude/settings.json"
        data = json.loads(settings.read_text())
        data["tui"] = "fullscreen"
        data["hooks"]["PreToolUse"].insert(0, FOREIGN)
        settings.write_text(json.dumps(data))
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        before = settings.read_text()

        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"MERGE +claude +~/.claude/settings.json")
        self.assertEqual(settings.read_text(), before)

        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        after = json.loads(settings.read_text())
        self.assertNotIn("hooks/ai-config", json.dumps(after))
        self.assertEqual(after["hooks"]["PreToolUse"], [FOREIGN])
        self.assertEqual(after["tui"], "fullscreen")
        self.assertTrue(list(settings.parent.glob("settings.json.bak-brainrc-*")))
        self.assertIn("Everything in sync.", quiet(brainrc.cmd_sync, False)[1])

    def test_uninstall_restores_the_settings_file(self):
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text('{"theme": "dark"}\n')
        quiet(brainrc.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(json.loads(settings.read_text()), {"theme": "dark"})

    def test_disabled_harness_without_settings_is_left_alone(self):
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".claude/settings.json").exists())

    def test_backups_are_capped(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        for n in range(brainrc.BACKUPS_KEPT + 3):
            (settings.parent / f"settings.json.bak-brainrc-2026010{n}T000000Z").write_text("{}")
        settings.write_text("{}")
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(len(list(settings.parent.glob("settings.json.bak-brainrc-*"))), brainrc.BACKUPS_KEPT)
        self.assertEqual(list(settings.parent.glob(".settings.json.brainrc-tmp*")), [])

    def test_checkout_hooks_link_into_the_checkout(self):
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(brainrc.link_target(self.home / ".claude/hooks/brainrc"), self.repo / "overrides/claude/hooks")
        self.assertFalse((self.settings_home / "hooks").exists())

    def test_temp_name_includes_the_pid(self):
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text("{}")
        names, real = [], os.replace

        def spy(src, dst):
            if Path(dst) == settings.resolve():
                names.append(Path(src).name)
            real(src, dst)

        with mock.patch("os.replace", spy):
            quiet(brainrc.cmd_sync, True)
        self.assertEqual(names, [f".settings.json.brainrc-tmp-{os.getpid()}"])

    @unittest.skipIf(os.name == "nt", "fcntl")
    def test_a_second_apply_fails_while_one_holds_the_lock(self):
        import fcntl
        lock = self.settings_home / "apply.lock"
        lock.parent.mkdir(parents=True)
        with open(lock, "a") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            code, out = quiet(brainrc.cmd_sync, True)
            status_code, status_out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 1, out)
        self.assertIn("another brainrc apply is running", out)
        self.assertIn("apply.lock", out)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.settings_home.iterdir()), [lock])
        self.assertEqual(status_code, 0, status_out)
        self.assertIn("Dry run", status_out)

    @unittest.skipIf(os.name == "nt", "fcntl")
    def test_the_lock_is_released_after_apply_even_on_error(self):
        import fcntl
        self.assertEqual(quiet(brainrc.cmd_sync, True)[0], 0)
        with mock.patch("brainrc.cli.plan", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                quiet(brainrc.cmd_sync, True)
        with open(self.settings_home / "apply.lock", "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)  # raises if a run leaked the lock
            fcntl.flock(f, fcntl.LOCK_UN)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)

    def test_settings_changed_during_apply_are_left_alone(self):
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text("{}")
        real = brainrc.cli.settings_change

        def harness_writes_meanwhile(m):
            result = real(m)
            if m.dest == settings:
                settings.write_text('{"theme": "app"}')
            return result

        with mock.patch("brainrc.cli.settings_change", harness_writes_meanwhile):
            code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"CHANGED +claude +~/.claude/settings.json")
        self.assertIn("close Claude Code", out)
        self.assertEqual(settings.read_text(), '{"theme": "app"}')
        self.assertEqual(list(settings.parent.glob("settings.json.bak-brainrc-*")), [])

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_settings_write_keeps_the_files_mode(self):
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir()
        for mode in (0o600, 0o640):
            settings.write_text("{}")
            settings.chmod(mode)
            quiet(brainrc.cmd_sync, True)
            self.assertIn("hooks", json.loads(settings.read_text()))
            self.assertEqual(stat.S_IMODE(settings.stat().st_mode), mode)
            newest = sorted(settings.parent.glob("settings.json.bak-brainrc-*"))[-1]
            self.assertEqual(stat.S_IMODE(newest.stat().st_mode), mode)

    @unittest.skipIf(os.name == "nt", "POSIX permission bits")
    def test_temp_file_is_never_looser_than_the_target(self):
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_text("{}")
        settings.chmod(0o600)
        seen, real = [], os.replace

        def spy(src, dst):
            if Path(dst) == settings.resolve():
                seen.append(stat.S_IMODE(os.stat(src).st_mode))
            real(src, dst)

        old = os.umask(0)  # a loose umask must not leak into the temp file
        try:
            with mock.patch("os.replace", spy):
                quiet(brainrc.cmd_sync, True)
        finally:
            os.umask(old)
        self.assertEqual(seen, [0o600])

    def test_symlinked_settings_stay_linked_and_the_target_gets_the_hooks(self):
        dotfiles = self.home / "dotfiles"
        dotfiles.mkdir()
        target = dotfiles / "settings.json"
        target.write_text('{"theme": "dark"}\n')
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir()
        settings.symlink_to(target)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue(settings.is_symlink())
        self.assertEqual(settings.readlink(), target)
        data = json.loads(target.read_text())
        self.assertEqual(data["theme"], "dark")
        self.assertIn("hooks", data)
        backups = list(dotfiles.glob("settings.json.bak-brainrc-*"))
        self.assertEqual([b.read_text() for b in backups], ['{"theme": "dark"}\n'])
        self.assertEqual(list(settings.parent.glob("settings.json.bak-brainrc-*")), [])
        self.assertEqual(list(self.home.rglob("*.brainrc-tmp")), [])

    def test_a_dangling_settings_link_creates_its_target(self):
        dotfiles = self.home / "dotfiles"
        dotfiles.mkdir()
        target = dotfiles / "settings.json"
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir()
        settings.symlink_to(target)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue(settings.is_symlink())
        self.assertEqual(settings.readlink(), target)
        self.assertIn("hooks", json.loads(target.read_text()))

    def test_apply_then_in_sync_and_conflicts_respected(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        settings.write_text(json.dumps({"hooks": {"SessionStart": [FOREIGN]}}))
        (self.home / ".codex").mkdir()
        (self.home / ".codex/AGENTS.md").write_text("mine\n")

        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1)  # the pre-existing codex file is a conflict
        self.assertIn("CONFLICT", out)
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text(), "mine\n")

        skill = self.home / ".claude/skills/spec-agent"
        self.assertTrue(skill.is_symlink())
        self.assertTrue((skill / "roles" / "implementer.md").is_file())
        self.assertTrue((self.home / ".claude/hooks/brainrc/guard_outward.py").is_file())

        merged = json.loads(settings.read_text())
        self.assertEqual(merged["hooks"]["SessionStart"], [FOREIGN])
        self.assertTrue(any(brainrc._owned(g) for g in merged["hooks"]["PreToolUse"]))
        self.assertEqual(len(list(settings.parent.glob("settings.json.bak-brainrc-*"))), 1)

        (self.home / ".codex/AGENTS.md").unlink()
        quiet(brainrc.cmd_sync, True)
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual((code, out.strip()), (0, "Everything in sync."))


PACK_TOML = '''\
name = "acme"
prefix = "acme-"
requires_core = ">=1.0, <2"

[[extensions.domains]]
files = "`deploy/*.yaml`"
skills = ["acme-deploy"]
reviewer = "infra-reviewer"

[[extensions.intake_context]]
skill = "acme-context"
when = "every ticket"

[extensions.ticket]
connector = "ticket-github"
refs = ["gh:*"]
draft = true

[extensions]
deliver_checks = ["Deploy plan reviewed"]
'''
PACK_FRAGMENT = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
    {"type": "command", "command": 'python3 "{{hooks_dir}}/guard_acme.py"'}]}]}}


def make_pack(root: Path, pack_toml: str = PACK_TOML) -> Path:
    def skill(name: str) -> None:
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Test skill {name}.\n---\nBody.\n")

    root.mkdir(parents=True, exist_ok=True)
    (root / "pack.toml").write_text(pack_toml)
    skill("acme-deploy")
    skill("acme-context")
    (root / "agents").mkdir()
    (root / "agents/acme-reviewer.md").write_text(
        "---\nname: acme-reviewer\ndescription: Reviews deploys.\ntools: Read, mcp__docs__search\n---\nReview.\n")
    (root / "rules").mkdir()
    (root / "rules/50-acme.md").write_text("# Acme\n\n- Acme rule.\n")
    hooks = root / "overrides/claude/hooks"
    hooks.mkdir(parents=True)
    (hooks / "guard_acme.py").write_text("print()\n")
    (root / "overrides/claude/settings.fragment.json").write_text(json.dumps(PACK_FRAGMENT))
    return root


class PackSyncTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")
        self.enable_pack()

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        shutil.rmtree(self.pack.parent)
        super().tearDown()

    def enable_pack(self, enabled: bool = True) -> None:
        (self.repo / "packs.local.toml").write_text(
            f'[acme]\npath = "{self.pack}"\nenabled = {str(enabled).lower()}\n')

    def settings_commands(self) -> list[str]:
        settings = json.loads((self.home / ".claude/settings.json").read_text())
        return [h["command"] for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]

    def test_apply_layers_pack_on_core(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        skills_dir = self.home / ".claude/skills"
        self.assertEqual(brainrc.link_target(skills_dir / "acme-deploy"), self.pack / "skills/acme-deploy")
        self.assertTrue((skills_dir / "spec-agent").is_symlink())
        self.assertTrue((self.home / ".claude/agents/acme-reviewer.md").is_symlink())

        rules = brainrc.rendered_instructions().read_text()
        self.assertLess(rules.index("# Security"), rules.index("- Acme rule."))

        hooks_link = self.home / ".claude/hooks/brainrc-acme"
        self.assertEqual(brainrc.link_target(hooks_link), self.pack / "overrides/claude/hooks")
        commands = self.settings_commands()
        self.assertIn(claude_guard("$HOME/.claude/hooks/brainrc", "guard_outward.py"), commands)
        self.assertIn('python3 "$HOME/.claude/hooks/brainrc-acme/guard_acme.py"', commands)

        ext = brainrc.extensions_file().read_text()
        for expected in ("| `deploy/*.yaml` | acme-deploy | infra-reviewer | acme |",
                         "- `acme-context` (acme): every ticket", '"connector": "ticket-github"',
                         "- (acme) Deploy plan reviewed"):
            self.assertIn(expected, ext)

        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual((code, out.strip()), (0, "Everything in sync."))

    def test_disabling_pack_removes_its_links_and_hooks(self):
        quiet(brainrc.cmd_sync, True)
        self.enable_pack(False)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".claude/skills/acme-deploy").is_symlink())
        self.assertFalse((self.home / ".claude/agents/acme-reviewer.md").is_symlink())
        self.assertFalse((self.home / ".claude/hooks/brainrc-acme").is_symlink())
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())
        commands = self.settings_commands()
        self.assertFalse(any("guard_acme" in c for c in commands))
        self.assertTrue(any("guard_outward" in c for c in commands))
        self.assertNotIn("- Acme rule.", brainrc.rendered_instructions().read_text())
        self.assertIn("No packs enabled", brainrc.extensions_file().read_text())

    def test_disabling_harness_prunes_its_links(self):
        quiet(brainrc.cmd_sync, True)
        self.assertTrue((self.home / ".cursor/skills/spec-agent").is_symlink())
        (self.repo / "harnesses.local.toml").write_text("[cursor]\nenabled = false\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(list((self.home / ".cursor/skills").iterdir()), [])

    def test_name_collision_writes_nothing(self):
        clash = self.pack / "skills/spec-agent"
        clash.mkdir()
        (clash / "SKILL.md").write_text("---\nname: spec-agent\ndescription: Clash.\n---\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1)
        self.assertIn("skill `spec-agent` is defined in both core and acme", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_pack_is_an_error(self):
        (self.repo / "packs.local.toml").write_text('[ghost]\npath = "/nonexistent/pack"\n')
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 1)
        self.assertIn("no pack.toml", out)

    def set_requires_core(self, line: str) -> None:
        set_requires_core(self.pack, line)

    def test_incompatible_pack_writes_nothing(self):
        self.set_requires_core('requires_core = ">=2.0"')
        for apply in (False, True):
            code, out = quiet(brainrc.cmd_sync, apply)
            self.assertEqual(code, 1, out)
            self.assertIn("acme:pack.toml: requires_core `>=2.0` is not satisfied by core 1.2.3", out)
            self.assertIn("Nothing written", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_disabled_incompatible_pack_is_not_checked(self):
        self.set_requires_core('requires_core = ">=2.0"')
        self.enable_pack(False)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("requires_core", out)

    def test_pack_without_requires_core_applies_with_warning(self):
        self.set_requires_core("")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn("WARN acme:pack.toml: no `requires_core`", out)
        self.assertIn('requires_core = ">=1.2, <2"', out)  # suggests the documented pin
        self.assertTrue((self.home / ".claude/skills/acme-deploy").is_symlink())

    def test_tokens_lists_pack_items(self):
        code, out = quiet(brainrc.cmd_tokens)
        self.assertEqual(code, 0)
        self.assertIn("acme:skills/acme-deploy", out)
        self.assertIn("Always loaded:", out)


def set_requires_core(pack: Path, line: str) -> None:
    """Replace the fixture's requires_core line (an empty line removes it)."""
    toml = pack / "pack.toml"
    old = 'requires_core = ">=1.0, <2"\n'
    assert old in toml.read_text(), "fixture no longer pins requires_core"
    toml.write_text(toml.read_text().replace(old, line + "\n" if line else ""))


def snapshot(*roots: Path) -> dict:
    """Every path under roots with its link target or size and mtime, to prove nothing changed."""
    seen = {}
    for root in roots:
        for path in sorted(root.rglob("*")):
            seen[path] = os.readlink(path) if path.is_symlink() else (path.lstat().st_size, path.lstat().st_mtime_ns)
    return seen


class DoctorTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        quiet(brainrc.cmd_sync, True)
        self.skills = self.home / ".claude/skills"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def doctor(self, expect_code: int | None = None) -> list[tuple[str, str, str]]:
        code, out = quiet(brainrc.cmd_doctor)
        if expect_code is not None:
            self.assertEqual(code, expect_code, out)
        return brainrc.doctor_findings()

    def assert_one_fail(self, what: str, fix: str) -> None:
        findings = self.doctor(1)
        fails = [f for f in findings if f[0] == "FAIL"]
        self.assertEqual(len(fails), 1, findings)
        self.assertIn(what, fails[0][1])
        self.assertIn(fix, fails[0][2])

    def test_clean_after_apply(self):
        code, out = quiet(brainrc.cmd_doctor)
        self.assertEqual(code, 0, out)
        self.assertIn("No problems found.", out)

    def test_missing_hook_script(self):
        (self.repo / "overrides/claude/hooks/guard_secrets.py").unlink()
        self.assert_one_fail("claude: hook missing: ~/.claude/hooks/brainrc/guard_secrets.py", "apply")

    def test_broken_hook_script(self):
        (self.repo / "overrides/claude/hooks/guard_outward.py").write_text("import sys\nsys.exit(3)\n")
        self.assert_one_fail("claude: hook ~/.claude/hooks/brainrc/guard_outward.py exits 3", "apply")

    def test_every_hook_runs_with_an_empty_payload(self):
        calls, real = [], subprocess.run

        def spy(args, **kw):
            calls.append((Path(args[-1]).name, kw.get("input"), kw.get("timeout")))
            return real(args, **kw)

        with mock.patch("brainrc.doctor.subprocess.run", spy):
            self.assertEqual([f for f in brainrc.doctor_findings() if "hook" in f[1]], [])
        self.assertIn(("guard_outward.py", "{}", 5), calls)
        self.assertIn(("guard_secrets.py", "{}", 5), calls)
        self.assertEqual([c for c in calls if c[0] == "guard.py"], [("guard.py", "{}", 5)])  # Cursor: once

    def test_points_to_troubleshooting_only_when_something_is_wrong(self):
        _, clean = quiet(brainrc.cmd_doctor)
        self.assertNotIn("troubleshooting", clean)
        (self.skills / "spec-agent").unlink()
        _, out = quiet(brainrc.cmd_doctor)
        self.assertIn("docs/troubleshooting.md", out.splitlines()[-1])
        self.assertTrue((REPO / "docs/troubleshooting.md").is_file())

    def test_writes_nothing(self):
        (self.repo / "rules/99-new.md").write_text("# New\n\n- Rule.\n")
        (self.skills / "spec-agent").unlink()
        (self.home / ".claude/settings.json").write_text("{}\n")
        before = snapshot(self.home, self.repo)
        self.doctor(1)
        self.assertEqual(snapshot(self.home, self.repo), before)

    def test_stale_render(self):
        (self.repo / "rules/99-new.md").write_text("# New\n\n- Rule.\n")
        self.assert_one_fail("instructions.md", "apply")

    def test_missing_render(self):
        brainrc.rendered_instructions().unlink()
        findings = self.doctor(1)
        self.assertTrue(any("instructions.md" in f[1] and "apply" in f[2] for f in findings), findings)

    def test_missing_link(self):
        (self.skills / "spec-agent").unlink()
        self.assert_one_fail("spec-agent", "apply")

    def test_many_missing_links_are_one_line(self):
        shutil.rmtree(self.skills)
        self.skills.mkdir()
        self.assert_one_fail("links are missing", "apply")

    def test_link_to_the_wrong_item(self):
        (self.skills / "spec-agent").unlink()
        (self.skills / "spec-agent").symlink_to(self.repo / "skills/terraform")
        self.assert_one_fail("spec-agent", "apply")

    def test_stale_link(self):
        (self.skills / "gone").symlink_to(self.repo / "skills/gone")
        self.assert_one_fail("gone", "apply")

    def test_broken_link_after_moving_the_repo(self):
        (self.skills / "spec-agent").unlink()
        (self.skills / "spec-agent").symlink_to("/nonexistent/old-checkout/skills/spec-agent")
        self.assert_one_fail("broken", "rm")

    def test_real_file_where_a_link_belongs(self):
        (self.skills / "spec-agent").unlink()
        (self.skills / "spec-agent").mkdir()
        self.assert_one_fail("not a link", "move")

    def test_harness_not_installed_warns(self):
        shutil.rmtree(self.home / ".cursor")
        findings = self.doctor(0)
        self.assertEqual([f[0] for f in findings], ["WARN"], findings)
        self.assertIn("cursor", findings[0][1])
        self.assertIn("[cursor] enabled = false", findings[0][2])
        self.assertIn("harnesses.local.toml", findings[0][2])

    def test_missing_pack_path(self):
        (self.repo / "packs.local.toml").write_text('[ghost]\npath = "/nonexistent/pack"\n')
        self.assert_one_fail("ghost", "packs")

    def test_incompatible_pack(self):
        pack = make_pack(self.home / "acme-pack")
        set_requires_core(pack, 'requires_core = ">=99"')
        (self.repo / "packs.local.toml").write_text(f'[acme]\npath = "{pack}"\n')
        findings = self.doctor(1)
        self.assertTrue(any(f[0] == "FAIL" and "acme" in f[1] and "requires_core" in f[1] for f in findings), findings)

    def test_hooks_left_in_a_disabled_harness(self):
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        findings = self.doctor(1)
        fails = [f for f in findings if f[0] == "FAIL" and "settings.json" in f[1]]
        self.assertEqual(len(fails), 1, findings)
        self.assertIn("claude is disabled", fails[0][1])
        self.assertIn("apply", fails[0][2])
        quiet(brainrc.cmd_sync, True)
        self.doctor(0)

    def test_broken_roles_link(self):
        roles = self.repo / "skills/spec-agent/roles"
        roles.unlink()
        roles.write_text("../../agents")
        findings = self.doctor(1)
        self.assertTrue(any(f[0] == "FAIL" and "roles" in f[1] and "Platforms" in f[2] for f in findings), findings)

    def test_unmerged_hooks(self):
        (self.home / ".claude/settings.json").write_text("{}\n")
        self.assert_one_fail("settings.json", "apply")

    def test_invalid_settings_json(self):
        (self.home / ".claude/settings.json").write_text("{not json\n")
        self.assert_one_fail("invalid JSON", "by hand")


class BudgetTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")
        self.core = brainrc.Source("core", self.repo)
        self.old_budget = brainrc.tokens.CORE_ALWAYS_BUDGET

    def tearDown(self):
        brainrc.tokens.CORE_ALWAYS_BUDGET = self.old_budget
        shutil.rmtree(self.pack.parent)
        super().tearDown()

    def check(self, *packs):
        return brainrc.check_budgets([self.core, *packs])

    def test_core_is_within_budget_with_no_warnings(self):
        total, items = brainrc.always_tokens(self.core)
        self.assertGreater(total, 1000)
        self.assertLessEqual(total, brainrc.tokens.CORE_ALWAYS_BUDGET)
        self.assertEqual(self.check(), ([], []))

    def test_always_tokens_counts_rules_and_descriptions(self):
        total, items = brainrc.always_tokens(self.core)
        labels = [label for _, label in items]
        self.assertIn("rules/30-guardrails.md", labels)
        self.assertIn("skills/spec-agent", labels)
        self.assertIn("agents/verifier.md", labels)
        self.assertIn("skills/work", labels)
        self.assertEqual(total, sum(n for n, _ in items))

    def test_core_over_budget_fails_naming_the_biggest_items(self):
        brainrc.tokens.CORE_ALWAYS_BUDGET = 100
        errors, _ = self.check()
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("core", errors[0])
        self.assertIn("budget 100", errors[0])
        _, items = brainrc.always_tokens(self.core)
        for _, label in sorted(items, reverse=True)[:3]:
            self.assertIn(label, errors[0])
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("budget 100", out)

    def test_pack_over_its_declared_budget_fails(self):
        toml = self.pack / "pack.toml"
        toml.write_text(toml.read_text().replace('prefix = "acme-"\n', 'prefix = "acme-"\nmax_always_tokens = 10\n'))
        errors, _ = self.check(brainrc.load_pack(self.pack))
        self.assertTrue(any("acme" in e and "budget 10" in e for e in errors), errors)

    def test_pack_without_a_budget_warns_above_the_default(self):
        (self.pack / "rules/50-acme.md").write_text("# Acme\n\n" + "- Rule text here.\n" * 300)
        errors, warnings = self.check(brainrc.load_pack(self.pack))
        self.assertEqual(errors, [])
        self.assertTrue(any("acme" in w and "max_always_tokens" in w for w in warnings), warnings)

    def test_long_description_warns(self):
        skill = self.pack / "skills/acme-deploy/SKILL.md"
        skill.write_text("---\nname: acme-deploy\ndescription: " + "word " * 120 + "\n---\nBody.\n")
        _, warnings = self.check(brainrc.load_pack(self.pack))
        self.assertTrue(any("acme:skills/acme-deploy" in w and "description" in w for w in warnings), warnings)

    def test_tokens_shows_budget_per_source(self):
        code, out = quiet(brainrc.cmd_tokens)
        self.assertEqual(code, 0)
        self.assertRegex(out, r"core: ~\d+ / 3000 always-loaded tokens")


class UnslopSplitTest(unittest.TestCase):
    SKILL = REPO / "skills/unslop"

    def test_no_rule_line_was_lost(self):
        text = "\n".join(p.read_text() for p in sorted(self.SKILL.rglob("*.md")))
        for line in (REPO / "tests/fixtures/unslop-rules.txt").read_text().splitlines():
            with self.subTest(line=line[:60]):
                self.assertIn(line, text)

    def test_skill_md_is_short_and_links_its_references(self):
        body = (self.SKILL / "SKILL.md").read_text()
        self.assertLess(len(body), 6000)
        for ref in ("structure.md", "clarity.md", "change-prose.md"):
            self.assertIn(f"references/{ref}", body)
        description = brainrc.frontmatter(self.SKILL / "SKILL.md")["description"]
        self.assertLessEqual(brainrc.estimate_tokens(description), 60)


class RolesLinkTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.roles = self.repo / "skills/spec-agent/roles"

    def assert_validate_fails(self):
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("skills/spec-agent/roles", out)
        self.assertIn("Platforms", out)

    def test_repo_link_passes(self):
        self.assertTrue(self.roles.is_symlink())
        self.assertIsNone(brainrc.check_roles_link())

    def test_plain_file_from_a_checkout_without_symlinks_fails(self):
        self.roles.unlink()
        self.roles.write_text("../../agents")  # what git writes when core.symlinks is false
        self.assert_validate_fails()

    def test_link_to_the_wrong_place_fails(self):
        self.roles.unlink()
        self.roles.symlink_to("../../skills")
        self.assert_validate_fails()


class PluginTest(TempRepoCase):
    def manifest(self, name="plugin.json"):
        return json.loads(brainrc.plugin_manifests()[f".claude-plugin/{name}"])

    def test_plugin_manifest_comes_from_the_repo(self):
        set_core_version(self.repo, "1.2.3")
        plugin = self.manifest()
        self.assertEqual((plugin["name"], plugin["version"]), ("brainrc", "1.2.3"))
        self.assertEqual(plugin["author"], {"name": "brainrc contributors"})
        commands = [h["command"] for groups in plugin["hooks"].values() for g in groups for h in g["hooks"]]
        self.assertIn(claude_guard("${CLAUDE_PLUGIN_ROOT}/overrides/claude/hooks", "guard_outward.py"), commands)
        self.assertNotIn("{{hooks_dir}}", json.dumps(plugin))

    def test_antigravity_manifest_is_the_name_only(self):
        self.assertEqual(json.loads(brainrc.plugin_manifests()["plugin.json"]), {"name": "brainrc"})

    def test_marketplace_lists_the_repo_as_the_plugin(self):
        market = self.manifest("marketplace.json")
        self.assertEqual(market["name"], "brainrc")
        self.assertEqual(f'{market["name"]}@{market["plugins"][0]["name"]}', "brainrc@brainrc")
        self.assertEqual(market["owner"], {"name": "brainrc contributors"})
        self.assertEqual(market["plugins"][0]["source"], ".")
        self.assertEqual(market["plugins"][0]["version"], self.manifest()["version"])

    def test_no_manifest_mentions_the_old_name(self):
        for rel, text in brainrc.plugin_manifests().items():
            self.assertNotIn("ai-config", text, rel)

    def test_old_name_manifest_is_stale(self):
        quiet(brainrc.cmd_plugin)
        path = self.repo / ".claude-plugin/plugin.json"
        path.write_text(path.read_text().replace('"brainrc"', '"ai-config"', 1))
        errors = brainrc.check_plugin()
        self.assertTrue(any("plugin.json" in e and "stale" in e and "brainrc.py plugin" in e for e in errors), errors)

    def test_plugin_command_writes_once(self):
        code, out = quiet(brainrc.cmd_plugin)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.repo / ".claude-plugin/plugin.json").is_file())
        self.assertTrue((self.repo / "plugin.json").is_file())
        self.assertEqual(brainrc.check_plugin(), [])
        code, out = quiet(brainrc.cmd_plugin)
        self.assertIn("up to date", out)

    def test_validate_fails_on_missing_or_stale_manifests(self):
        self.assertEqual(brainrc.check_plugin(), [])  # no .claude-plugin/: this repo doesn't publish one
        quiet(brainrc.cmd_plugin)
        (self.repo / ".claude-plugin/marketplace.json").unlink()
        errors = brainrc.check_plugin()
        self.assertTrue(any("marketplace.json" in e and "missing" in e and "brainrc.py plugin" in e for e in errors), errors)
        quiet(brainrc.cmd_plugin)
        set_core_version(self.repo, "9.9.9")
        errors = brainrc.check_plugin()
        self.assertTrue(any("plugin.json" in e and "stale" in e for e in errors), errors)
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("brainrc.py plugin", out)


class SettingsHomeTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def test_defaults_to_config_dir_under_home(self):
        os.environ.pop("BRAINRC_HOME")
        with mock.patch.dict(os.environ):
            os.environ.pop("XDG_CONFIG_HOME", None)  # CI runners set it
            self.assertEqual(brainrc.settings_home(), self.home / ".config/brainrc")

    def test_removed_names_are_gone(self):
        for mod in (brainrc, brainrc.config, brainrc.cli):
            for name in ("aicfg_home", "SHIM_REMOVED_IN", "warn_deprecated", "warn_home"):
                self.assertFalse(hasattr(mod, name), (mod.__name__, name))

    def test_aicfg_home_is_not_read(self):
        os.environ.pop("BRAINRC_HOME")
        with mock.patch.dict(os.environ, {"AICFG_HOME": str(self.home / "old")}):
            os.environ.pop("XDG_CONFIG_HOME", None)
            self.assertEqual(brainrc.settings_home(), self.home / ".config/brainrc")

    def test_apply_renders_into_settings_home(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.settings_home / "instructions.md").is_file())
        self.assertTrue((self.settings_home / "extensions.md").is_file())
        self.assertTrue(brainrc.extensions_file().is_file())  # deprecated in-repo copy, kept for packs
        self.assertEqual(brainrc.link_target(self.home / ".claude/CLAUDE.md"), self.settings_home / "instructions.md")
        self.assertFalse((self.repo / "dist/instructions.md").exists())

    def test_old_dist_link_is_updated_and_old_file_removed(self):
        old = self.repo / "dist/instructions.md"
        old.parent.mkdir()
        old.write_text("old render\n")
        link = self.home / ".claude/CLAUDE.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(old)
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertRegex(out, r"UPDATE +claude +~/.claude/CLAUDE.md")
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(brainrc.link_target(link), self.settings_home / "instructions.md")
        self.assertFalse(old.parent.exists())  # the emptied dist/ goes too

    def test_disabled_harness_link_to_settings_home_is_pruned(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".claude/CLAUDE.md").is_symlink())

    def test_doctor_names_the_home_render(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "rules/99-new.md").write_text("# New\n\n- Rule.\n")
        fails = [f for f in brainrc.doctor_findings() if f[0] == "FAIL"]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn(brainrc.tilde(self.settings_home / "instructions.md"), fails[0][1])


class UserInvokedSkillTest(unittest.TestCase):
    """Codex skips commands that use $ARGUMENTS, so core ships them as user-invoked skills."""

    def test_core_has_no_commands_folder(self):
        self.assertFalse((REPO / "commands").exists())

    def test_skills_taking_arguments_are_user_invoked(self):
        for skill in sorted((REPO / "skills").glob("*/SKILL.md")):
            if "$ARGUMENTS" not in skill.read_text():
                continue
            with self.subTest(skill=skill.parent.name):
                meta = brainrc.frontmatter(skill)
                self.assertEqual(meta.get("disable-model-invocation"), "true")
                self.assertTrue(meta.get("argument-hint"))


class PythonVersionTest(unittest.TestCase):
    def test_old_python_gets_a_message_not_a_traceback(self):
        # Hiding tomllib is what Python 3.10 looks like to the script.
        code = ("import runpy, sys; sys.modules['tomllib'] = None; sys.argv = ['brainrc.py', 'status']; "
                f"runpy.run_path({str(REPO / 'scripts/brainrc.py')!r}, run_name='__main__')")
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("needs Python 3.11+", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class VersionConstraintTest(unittest.TestCase):
    def test_satisfies(self):
        cases = [
            ((1, 2, 3), ">=1.0", True),
            ((1, 2, 3), ">=1.0, <2", True),
            ((2, 0, 0), ">=1.0, <2", False),
            ((1, 2, 3), "1.2", True),          # bare version means >=
            ((1, 1, 9), "1.2", False),
            ((1, 2, 0), "==1.2", True),        # missing parts are zero
            ((1, 2, 3), "==1.2.3", True),
            ((1, 2, 3), "!=1.2.3", False),
            ((1, 2, 0), ">1.2", False),
            ((1, 2, 0), "<=1.2.0", True),
            ((0, 9, 0), " >= 0.1 ,< 1 ", True),
        ]
        for version, text, expected in cases:
            with self.subTest(text=text, version=version):
                self.assertEqual(brainrc.satisfies(version, brainrc.parse_constraint(text)), expected)

    def test_rejects_malformed(self):
        for text in ("latest", ">>1", "", ">=0.1,", "=>0.1", "1.2.3.4", ">=1.x", "^1.2", "~=1.2"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                brainrc.parse_constraint(text)


class RenderInstructionsTest(TempRepoCase):
    """Rule order: core (unlabelled), then one labelled block per pack in source order, then local."""

    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.acme = make_pack(self.tmp / "acme-pack")
        (self.acme / "rules/15-acme.md").write_text("# Early acme\n\n- Early acme rule.\n")
        beta = self.tmp / "beta-pack"
        (beta / "rules").mkdir(parents=True)
        (beta / "pack.toml").write_text('name = "beta"\nrequires_core = ">=0"\n')
        (beta / "rules/10-beta.md").write_text("# Beta\n\n- Beta rule.\n")
        self.core = brainrc.Source("core", self.repo)
        self.srcs = [self.core, brainrc.load_pack(self.acme), brainrc.load_pack(beta)]

    def tearDown(self):
        shutil.rmtree(self.tmp)
        super().tearDown()

    def last_core_rule(self, out: str) -> int:
        last = brainrc.rule_text(brainrc.markdown_files("rules", self.core)[-1])
        return out.index(last) + len(last)

    def test_core_only_render_is_unchanged(self):
        texts = [brainrc.rule_text(p) for p in sorted((self.repo / "rules").glob("*.md"))]
        expected = ("<!-- GENERATED by brainrc from rules/*.md (core). Edit the source repo, "
                    "not this file. -->\n\n" + "\n\n".join(texts) + "\n")
        self.assertEqual(brainrc.render_instructions([self.core]), expected)

    def test_pack_rules_follow_every_core_rule(self):
        out = brainrc.render_instructions(self.srcs)
        self.assertLess(self.last_core_rule(out), out.index("- Early acme rule."))

    def test_pack_blocks_are_labelled_in_source_order(self):
        out = brainrc.render_instructions(self.srcs)
        acme, beta = out.index("<!-- pack: acme -->"), out.index("<!-- pack: beta -->")
        self.assertLess(self.last_core_rule(out), acme)
        self.assertLess(acme, out.index("- Early acme rule."))
        self.assertLess(out.index("- Acme rule."), beta)  # acme's block ends before beta's starts
        self.assertLess(beta, out.index("- Beta rule."))
        self.assertIn("Rules from pack acme. They refine the rules above and never override them.", out)
        self.assertNotIn("<!-- pack: core -->", out)

    def test_local_rules_render_last_under_a_label(self):
        (self.repo / "rules/99-mine.local.md").write_text("- My local rule.\n")
        (self.acme / "rules/01-acme.local.md").write_text("- Acme local rule.\n")
        out = brainrc.render_instructions(self.srcs)
        local = out.index("<!-- local -->")
        self.assertLess(out.index("- Beta rule."), local)
        self.assertLess(local, out.index("- Acme local rule."))
        self.assertLess(out.index("- Acme local rule."), out.index("- My local rule."))  # by filename
        self.assertIn("Machine-local rules. They refine the rules above and never override them.", out)


class RuleFrontmatterTest(TempRepoCase):
    """Antigravity drops rules without a `trigger`; other harnesses must never see it."""

    def test_rule_text_strips_frontmatter(self):
        rule = self.repo / "rules/50-x.md"
        rule.write_text("---\ntrigger: always_on\n---\n\n# X\n\n- X rule.\n")
        self.assertEqual(brainrc.rule_text(rule), "# X\n\n- X rule.")
        plain = self.repo / "rules/51-y.md"
        plain.write_text("# Y\n\n- Y rule.\n")
        self.assertEqual(brainrc.rule_text(plain), "# Y\n\n- Y rule.")

    def test_render_and_budget_leave_out_the_trigger(self):
        out = brainrc.render_instructions()
        self.assertIn("# Working agreements", out)
        self.assertNotIn("trigger:", out)
        _, items = brainrc.always_tokens(brainrc.Source("core", self.repo))
        rule = self.repo / "rules/00-core.md"
        self.assertIn((brainrc.estimate_tokens(brainrc.rule_text(rule)), "rules/00-core.md"), items)

    def test_core_rules_need_a_trigger(self):
        (self.repo / "rules/50-x.md").write_text("# X\n\n- X rule.\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("rules/50-x.md", out)
        self.assertIn("trigger", out)


class OpenCodeAgentTest(TempRepoCase):
    """OpenCode rejects Claude's agent frontmatter, so apply renders its own copies (#19)."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        self.agents = self.home / ".config/opencode/agents"
        self.renders = self.settings_home / "opencode/agents"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def write_agent(self, name: str, meta: str) -> Path:
        path = self.repo / "agents" / f"{name}.md"
        path.write_text(f"---\nname: {name}\ndescription: Fixture agent.\n{meta}---\n\n## Role\nBody.\n")
        return path

    def test_tools_become_denies_and_model_is_dropped(self):
        out = brainrc.opencode_agent(self.write_agent("fixture", "tools: Read, Grep\nmodel: sonnet\n"))
        self.assertTrue(out.startswith("---\nname: fixture\ndescription: Fixture agent.\nmode: subagent\n"), out)
        self.assertTrue(out.endswith("---\n\n## Role\nBody.\n"), out)
        for key in ("edit", "bash", "glob", "webfetch", "websearch", "task", "todowrite"):
            self.assertIn(f"\n  {key}: deny\n", out)
        for key in ("read", "grep", "list"):
            self.assertNotIn(f"  {key}: deny", out)
        self.assertNotIn("model", out)
        self.assertNotIn("tools", out)

    def test_agent_without_tools_keeps_every_permission(self):
        out = brainrc.opencode_agent(self.write_agent("open", ""))
        self.assertNotIn("permission", out)
        self.assertIn("mode: subagent", out)

    def test_apply_links_rendered_agents(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        link = self.agents / "analyst.md"
        self.assertEqual(brainrc.link_target(link), self.renders / "analyst.md")
        self.assertIn("mode: subagent", link.read_text())
        self.assertEqual(brainrc.link_target(self.home / ".claude/agents/analyst.md"), self.repo / "agents/analyst.md")
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_removed_agent_is_pruned(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "agents/verifier.md").unlink()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.agents / "verifier.md").is_symlink())
        self.assertFalse((self.renders / "verifier.md").exists())

    def test_doctor_flags_a_stale_render(self):
        quiet(brainrc.cmd_sync, True)
        (self.renders / "analyst.md").write_text("old\n")
        fails = [f for f in brainrc.doctor_findings() if f[0] == "FAIL"]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("opencode/agents/analyst.md is stale", fails[0][1])

    def test_unknown_agents_format_is_an_error(self):
        (self.repo / "harnesses.local.toml").write_text('[opencode]\nagents_format = "nope"\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("agents_format", out)


class CrashRegressionTest(TempRepoCase):
    """Problems the Rust parity work found brainrc crashing on instead of reporting."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def test_dangling_markdown_link_in_a_skill_is_reported(self):
        (self.repo / "skills/terraform/gone.md").symlink_to(self.repo / "nowhere.md")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("skills/terraform/gone.md: dangling symlink", out)
        code, out = quiet(brainrc.cmd_tokens)
        self.assertEqual(code, 0, out)

    def break_fragment(self):
        fragment = self.repo / "overrides/claude/settings.fragment.json"
        fragment.write_text('{"hooks": {,}}\n')
        return "overrides/claude/settings.fragment.json: invalid JSON"

    def test_invalid_fragment_stops_apply_before_writing(self):
        error = self.break_fragment()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn(f"ERROR {error}", out)
        self.assertIn("Nothing written", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_invalid_fragment_is_a_doctor_finding(self):
        quiet(brainrc.cmd_sync, True)
        error = self.break_fragment()
        fails = [f[1] for f in brainrc.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any(error in f for f in fails), fails)

    def test_invalid_fragment_in_plugin_and_validate(self):
        (self.repo / ".claude-plugin").mkdir()
        error = self.break_fragment()
        code, out = quiet(brainrc.cmd_plugin)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR", out)
        self.assertIn("invalid JSON", out)
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.count(error), 1, out)

    def test_unknown_agents_format_is_a_doctor_finding(self):
        (self.repo / "harnesses.local.toml").write_text('[opencode]\nagents_format = "nope"\n')
        fails = [f for f in brainrc.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any("agents_format" in what and "opencode" in fix for _, what, fix in fails), fails)

    def test_new_hook_events_keep_fragment_order(self):
        events = ["Stop", "SessionStart", "PostToolUse", "Notification", "UserPromptSubmit",
                  "PreCompact", "SubagentStop", "SessionEnd"]
        group = {"hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/ai-config/x.py"}]}
        fragment = {"hooks": {e: [group] for e in events}}
        merged = brainrc.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, fragment)
        self.assertEqual(list(merged["hooks"]), ["PreToolUse", *events])


class HookDirRenameTest(PackSyncTest):
    """An old-name install (hooks/ai-config*) converges on hooks/brainrc* with one apply."""

    def old_install(self):
        hooks = self.home / ".claude/hooks"
        hooks.mkdir(parents=True)
        (hooks / "ai-config").symlink_to(self.core_hooks())
        (hooks / "ai-config-acme").symlink_to(self.pack / "overrides/claude/hooks")
        old = [{"matcher": "Bash", "hooks": [{"type": "command", "command": f"python3 $HOME/.claude/hooks/{d}/x.py"}]}
               for d in ("ai-config", "ai-config-acme")]
        (self.home / ".claude/settings.json").write_text(json.dumps({"hooks": {"PreToolUse": old}}))
        return hooks

    def core_hooks(self) -> Path:
        return self.repo / "overrides/claude/hooks"

    def test_fresh_apply_makes_only_brainrc_links(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        hooks = self.home / ".claude/hooks"
        self.assertEqual(sorted(p.name for p in hooks.iterdir()), ["brainrc", "brainrc-acme"])
        self.assertTrue((self.home / ".cursor/hooks/brainrc").is_symlink())
        self.assertNotIn("hooks/ai-config", (self.home / ".claude/settings.json").read_text())

    def test_old_links_are_removed_and_settings_rewritten_once(self):
        hooks = self.old_install()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(sorted(p.name for p in hooks.iterdir()), ["brainrc", "brainrc-acme"])
        commands = self.settings_commands()
        self.assertNotIn("hooks/ai-config", " ".join(commands))
        self.assertEqual(len(commands), len(set(commands)))
        self.assertEqual(sum("guard_acme" in c for c in commands), 1)
        self.assertEqual(sum("guard_outward" in c for c in commands), 1)
        self.assertEqual(quiet(brainrc.cmd_sync, False)[1].strip(), "Everything in sync.")

    def test_cursor_old_link_is_removed(self):
        hooks = self.home / ".cursor/hooks"
        hooks.mkdir(parents=True)
        (hooks / "ai-config").symlink_to(self.repo / "overrides/cursor/hooks")
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(sorted(p.name for p in hooks.iterdir()), ["brainrc"])

    def test_real_dir_or_file_at_the_old_name_is_left_alone(self):
        hooks = self.home / ".claude/hooks"
        (hooks / "ai-config").mkdir(parents=True)
        (hooks / "ai-config/mine.py").write_text("x\n")
        (hooks / "ai-config-acme").write_text("mine\n")
        quiet(brainrc.cmd_sync, True)
        self.assertEqual((hooks / "ai-config/mine.py").read_text(), "x\n")
        self.assertEqual((hooks / "ai-config-acme").read_text(), "mine\n")

    def test_old_symlink_to_a_foreign_target_is_left_alone(self):
        hooks = self.home / ".claude/hooks"
        hooks.mkdir(parents=True)
        mine = self.home / "my-hooks"
        mine.mkdir()
        (hooks / "ai-config").symlink_to(mine)
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(brainrc.link_target(hooks / "ai-config"), mine)

    def test_old_link_into_a_former_home_copy_is_removed(self):
        legacy = self.home / ".config/ai-config"
        copy = legacy / "hooks/core/claude/hooks"
        copy.mkdir(parents=True)
        hooks = self.home / ".claude/hooks"
        hooks.mkdir(parents=True)
        (hooks / "ai-config").symlink_to(copy)
        quiet(brainrc.cmd_sync, True)
        self.assertFalse((hooks / "ai-config").is_symlink())
        self.assertTrue(copy.is_dir())  # former-home copies are left for migrate

    def test_custom_hooks_dir_is_used_as_given_and_siblings_are_untouched(self):
        (self.repo / "harnesses.local.toml").write_text('[claude]\nhooks_dir = "~/.claude/hooks/mine"\n')
        hooks = self.old_install()
        quiet(brainrc.cmd_sync, True)
        self.assertEqual(sorted(p.name for p in hooks.iterdir()),
                         ["ai-config", "ai-config-acme", "mine", "mine-acme"])
        self.assertEqual(brainrc.link_target(hooks / "ai-config"), self.core_hooks())


class InstalledModeTest(TempRepoCase):
    """brainrc installed with pipx/uv: core comes bundled as brainrc/_core and is never written to."""

    def setUp(self):
        super().setUp()
        self.pkg = Path(tempfile.mkdtemp()) / "brainrc"
        self.core = self.pkg / "_core"
        copy_repo(self.core)
        roles = self.core / "skills/spec-agent/roles"
        roles.unlink()
        shutil.copytree(self.core / "agents", roles)  # wheels copy the link's files
        brainrc.config.REPO = self.core
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        shutil.rmtree(self.pkg.parent)
        super().tearDown()

    def files(self) -> list[str]:
        return sorted(str(p.relative_to(self.core)) for p in self.core.rglob("*"))

    def test_bundled_core_is_found_next_to_the_package(self):
        self.assertEqual(brainrc.config.find_core(self.pkg), self.core)
        self.assertEqual(brainrc.config.find_core(self.repo / "brainrc"), self.repo)
        self.assertTrue(brainrc.config.installed())

    def test_local_files_live_in_settings_home(self):
        self.settings_home.mkdir(parents=True)
        (self.settings_home / "harnesses.local.toml").write_text("[cursor]\nenabled = false\n")
        (self.core / "harnesses.local.toml").write_text("[codex]\nenabled = false\n")
        harnesses = brainrc.config.load_harnesses()
        self.assertNotIn("cursor", harnesses)
        self.assertIn("codex", harnesses)
        (self.settings_home / "rules").mkdir()
        (self.settings_home / "rules/99-mine.local.md").write_text("- My local rule.\n")
        self.assertIn("- My local rule.", brainrc.render_instructions())

    def test_apply_never_writes_inside_the_package(self):
        (self.core / "skills/spec-agent/references/extensions.md").unlink(missing_ok=True)
        before = self.files()
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.files(), before)
        self.assertTrue((self.settings_home / "extensions.md").is_file())
        self.assertEqual(brainrc.link_target(self.home / ".claude/skills/spec-agent"), self.core / "skills/spec-agent")
        self.assertEqual(brainrc.doctor_findings(), [])

    def copy_root(self) -> Path:
        return self.settings_home / "hooks/core"

    def test_installed_hooks_link_into_a_copy_in_settings_home(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        for harness in ("claude", "cursor"):
            copy = self.copy_root() / harness / "hooks"
            self.assertEqual(brainrc.link_target(self.home / f".{harness}/hooks/brainrc"), copy)
            self.assertEqual(sorted(p.name for p in copy.iterdir()),
                             sorted(p.name for p in (self.core / "overrides" / harness / "hooks").iterdir()))
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_guards_still_run_after_the_package_is_gone(self):
        quiet(brainrc.cmd_sync, True)
        claude = json.loads((self.home / ".claude/settings.json").read_text())
        cursor = json.loads((self.home / ".cursor/hooks.json").read_text())
        shutil.rmtree(self.core)  # an upgrade to a new Python moved the package
        risky = {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}}
        run = subprocess.run(["sh", "-c", claude["hooks"]["PreToolUse"][0]["hooks"][0]["command"]],
                             input=json.dumps(risky), capture_output=True, text=True)
        self.assertEqual(json.loads(run.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")
        shell = {"hook_event_name": "beforeShellExecution", "command": "git push origin main", "cwd": "/tmp/p"}
        run = subprocess.run(["sh", "-c", cursor["hooks"]["beforeShellExecution"][0]["command"]],
                             input=json.dumps(shell), capture_output=True, text=True)
        self.assertEqual(json.loads(run.stdout)["permission"], "deny")

    def test_an_upgraded_package_refreshes_the_copy(self):
        quiet(brainrc.cmd_sync, True)
        (self.copy_root() / "claude/hooks/leftover.py").write_text("")
        guard = self.core / "overrides/claude/hooks/guard_outward.py"
        guard.write_text(guard.read_text() + "\n# upgraded\n")
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertRegex(out, r"UPDATE +claude +~/.claude/hooks/brainrc")
        quiet(brainrc.cmd_sync, True)
        self.assertEqual((self.copy_root() / "claude/hooks/guard_outward.py").read_text(), guard.read_text())
        self.assertFalse((self.copy_root() / "claude/hooks/leftover.py").exists())
        self.assertIn("Everything in sync", quiet(brainrc.cmd_sync, False)[1])

    def test_an_old_link_into_the_package_is_repointed(self):
        link = self.home / ".claude/hooks/brainrc"
        link.parent.mkdir(parents=True)
        link.symlink_to(self.core / "overrides/claude/hooks")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"UPDATE +claude +~/.claude/hooks/brainrc")
        self.assertEqual(brainrc.link_target(link), self.copy_root() / "claude/hooks")
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_disabling_every_hooked_harness_removes_the_copy(self):
        quiet(brainrc.cmd_sync, True)
        local = self.settings_home / "harnesses.local.toml"
        local.write_text("[cursor]\nenabled = false\n")
        quiet(brainrc.cmd_sync, True)
        self.assertFalse((self.home / ".cursor/hooks/brainrc").is_symlink())
        self.assertTrue(self.copy_root().is_dir())  # claude still links into it
        local.write_text("[cursor]\nenabled = false\n[claude]\nenabled = false\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"PRUNE +~?.*hooks/core")
        self.assertFalse((self.home / ".claude/hooks/brainrc").is_symlink())
        self.assertFalse(self.copy_root().exists())

    def test_relative_pack_path_is_relative_to_settings_home(self):
        self.settings_home.mkdir(parents=True)
        shutil.copytree(REPO / "examples/pack-acme", self.settings_home / "packs/acme")
        (self.settings_home / "packs.local.toml").write_text('[acme]\npath = "packs/acme"\n')
        self.assertEqual([s.root for s in brainrc.sources()][-1], self.settings_home / "packs/acme")

    def test_hints_name_the_installed_command(self):
        fixes = [fix for _, _, fix in brainrc.doctor_findings()]  # nothing applied yet
        self.assertIn("brainrc apply", fixes)
        self.assertFalse(any("scripts/brainrc.py" in f for f in fixes), fixes)
        code, out = quiet(brainrc.main, ["brainrc", "bogus"])
        self.assertEqual(code, 2)
        self.assertIn("  brainrc status", out)
        self.assertNotIn("brainrc.py", out)

    def test_plugin_needs_a_checkout(self):
        code, out = quiet(brainrc.cmd_plugin)
        self.assertEqual(code, 1, out)
        self.assertIn("checkout", out)

    def test_copied_roles_are_fine_when_installed(self):
        self.assertIsNone(brainrc.check_roles_link())

    def test_tokens_match_a_checkout(self):
        _, installed = quiet(brainrc.cmd_tokens)
        brainrc.config.REPO = self.repo
        _, checkout = quiet(brainrc.cmd_tokens)
        self.assertEqual(installed, checkout)


def git(*args, cwd=None):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   cwd=cwd, check=True, capture_output=True)


class GitPackTest(TempRepoCase):
    """A pack named by git URL: brainrc fetches it into $BRAINRC_HOME/packs/<key> (#50)."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        self.tmp = Path(tempfile.mkdtemp())
        work = self.tmp / "work"
        shutil.copytree(REPO / "examples/pack-acme", work)
        git("init", "-q", cwd=work)
        git("add", ".", cwd=work)
        git("commit", "-qm", "v1", cwd=work)
        git("tag", "v1", cwd=work)
        new = work / "skills/acme-new"
        shutil.copytree(work / "skills/acme-context", new)
        skill = new / "SKILL.md"
        skill.write_text(skill.read_text().replace("name: acme-context", "name: acme-new"))
        git("add", ".", cwd=work)
        git("commit", "-qm", "v2", cwd=work)
        git("tag", "v2", cwd=work)
        git("clone", "-q", "--bare", str(work), str(self.tmp / "acme.git"))
        self.url = (self.tmp / "acme.git").as_uri()
        self.clone = self.settings_home / "packs/acme"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        shutil.rmtree(self.tmp)
        super().tearDown()

    def use(self, **keys):
        lines = "".join(f'{k} = "{v}"\n' for k, v in keys.items())
        (self.repo / "packs.local.toml").write_text(f"[acme]\n{lines}")

    def test_apply_fetches_and_links(self):
        self.use(git=self.url, ref="v1")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn(f"FETCH     acme      {self.url} (v1)", out)
        self.assertTrue((self.clone / "pack.toml").is_file())
        self.assertTrue((self.home / ".claude/skills/acme-context").is_symlink())
        self.assertFalse((self.home / ".claude/skills/acme-new").exists())
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_status_does_not_fetch(self):
        self.use(git=self.url)
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertIn("FETCH", out)
        self.assertFalse(self.clone.exists())

    def test_update_moves_to_a_new_ref(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        self.use(git=self.url, ref="v2")
        code, out = quiet(brainrc.cmd_update)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.home / ".claude/skills/acme-new").is_symlink())

    def test_failed_fetch_writes_nothing(self):
        self.use(git=(self.tmp / "missing.git").as_uri())
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR", out)
        self.assertIn("Nothing written", out)
        self.assertFalse(self.clone.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_update_leaves_a_changed_clone_alone(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        (self.clone / "pack.toml").write_text((self.clone / "pack.toml").read_text() + "# mine\n")
        code, out = quiet(brainrc.cmd_update)
        self.assertEqual(code, 1, out)
        self.assertIn("local changes", out)
        self.assertTrue((self.clone / "pack.toml").read_text().endswith("# mine\n"))

    def test_path_and_git_together_is_an_error(self):
        self.use(git=self.url, path="somewhere")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("`path` or `git`", out)

    def test_url_that_looks_like_an_option_is_refused(self):
        self.use(git="--upload-pack=touch x")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR", out)

    def test_apply_follows_a_ref_change(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        self.use(git=self.url, ref="v2")
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertIn(f"FETCH     acme      {self.url} (v2)", out)
        self.assertFalse((self.clone / "skills/acme-new").exists())  # status doesn't fetch
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn("FETCH", out)
        self.assertTrue((self.clone / "skills/acme-new").is_dir())
        self.assertTrue((self.home / ".claude/skills/acme-new").is_symlink())

    def test_apply_follows_a_url_change(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        moved = self.tmp / "moved.git"
        shutil.copytree(self.tmp / "acme.git", moved)
        shutil.rmtree(self.tmp / "acme.git")
        self.use(git=moved.as_uri(), ref="v2")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn(f"FETCH     acme      {moved.as_uri()} (v2)", out)
        self.assertTrue((self.clone / "skills/acme-new").is_dir())

    def test_doctor_flags_a_clone_that_doesnt_match(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        self.use(git=self.url, ref="v2")
        fails = [f for f in brainrc.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any("v1" in what and "v2" in what and "apply" in fix for _, what, fix in fails), fails)

    def test_unchanged_config_does_not_fetch(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        with mock.patch("brainrc.packs.subprocess.run") as run:
            code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("FETCH", out)
        run.assert_not_called()

    def test_a_clone_without_a_record_is_fetched_once(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        record = self.clone / ".git/brainrc-fetched.json"
        self.assertTrue(record.is_file())
        record.unlink()  # as a clone from before brainrc recorded fetches
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertIn("FETCH", out)
        quiet(brainrc.cmd_sync, True)
        self.assertTrue(record.is_file())
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertNotIn("FETCH", out)

    def test_an_old_record_is_read_then_replaced_by_the_new_one(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        new, old = self.clone / ".git/brainrc-fetched.json", self.clone / ".git/aicfg-fetched.json"
        new.rename(old)
        with mock.patch("brainrc.packs.subprocess.run") as run:
            code, out = quiet(brainrc.cmd_sync, False)
        self.assertNotIn("FETCH", out)
        run.assert_not_called()
        self.assertTrue(old.is_file())  # status writes nothing
        with mock.patch("brainrc.packs.subprocess.run") as run:
            code, out = quiet(brainrc.cmd_sync, True)
        run.assert_not_called()
        self.assertTrue(new.is_file())
        self.assertFalse(old.exists())
        self.assertIsNone(brainrc.packs.needs_fetch({"git": self.url, "ref": "v1"}, self.clone))

    def test_apply_leaves_only_a_valid_new_record(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        new, old = self.clone / ".git/brainrc-fetched.json", self.clone / ".git/aicfg-fetched.json"
        for broken in ("not json", None):  # a corrupt new record; a stale old one beside a valid new one
            old.write_text(new.read_text())
            if broken:
                new.write_text(broken)
            with mock.patch("brainrc.packs.subprocess.run") as run:
                quiet(brainrc.cmd_sync, True)
            run.assert_not_called()
            self.assertFalse(old.exists())
            self.assertEqual(json.loads(new.read_text()), {"git": self.url, "ref": "v1"})

    def test_a_mismatching_old_record_still_fetches(self):
        self.use(git=self.url, ref="v1")
        quiet(brainrc.cmd_sync, True)
        (self.clone / ".git/brainrc-fetched.json").unlink()
        (self.clone / ".git/aicfg-fetched.json").write_text('{"git": "elsewhere", "ref": "v1"}\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertIn("FETCH", out)
        self.assertFalse((self.clone / ".git/aicfg-fetched.json").exists())
        self.assertTrue((self.clone / ".git/brainrc-fetched.json").is_file())

    def test_a_hung_git_call_times_out(self):
        self.use(git=self.url, ref="v1")
        timeout = subprocess.TimeoutExpired(["git", "fetch"], 60)
        with mock.patch("brainrc.packs.subprocess.run", side_effect=timeout):
            code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR git init timed out after 60s", out)
        self.assertIn("Nothing written", out)
        self.assertFalse(self.clone.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_git_calls_have_a_timeout(self):
        self.use(git=self.url, ref="v1")
        real = subprocess.run
        with mock.patch("brainrc.packs.subprocess.run", side_effect=real) as run:
            quiet(brainrc.cmd_sync, True)
        self.assertTrue(run.call_args_list)
        self.assertTrue(all(c.kwargs.get("timeout") == 60 for c in run.call_args_list), run.call_args_list)

    def test_doctor_flags_an_unfetched_pack(self):
        self.use(git=self.url)
        fails = [f for f in brainrc.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any("not fetched" in what for _, what, _ in fails), fails)


class HarnessPluginTest(TempRepoCase):
    """A harness `plugin` key links overrides/<harness>/plugin.js (OpenCode's guard plugin)."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        self.link = self.home / ".config/opencode/plugins/brainrc-guard.js"
        self.old_link = self.home / ".config/opencode/plugins/ai-config-guard.js"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def test_apply_links_the_plugin_and_doctor_is_clean(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(brainrc.link_target(self.link), self.repo / "overrides/opencode/plugin.js")
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_apply_replaces_the_old_guard_link(self):
        self.old_link.parent.mkdir(parents=True)
        self.old_link.symlink_to(self.repo / "overrides/opencode/plugin.js")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(brainrc.link_target(self.link), self.repo / "overrides/opencode/plugin.js")
        self.assertFalse(self.old_link.is_symlink())
        self.assertEqual(brainrc.doctor_findings(), [])
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertIn("in sync", out.lower())

    def test_a_real_file_at_the_old_guard_path_is_left_alone(self):
        self.old_link.parent.mkdir(parents=True)
        self.old_link.write_text("// mine\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.old_link.read_text(), "// mine\n")
        self.assertTrue(self.link.is_symlink())

    def test_a_foreign_symlink_at_the_old_guard_path_is_left_alone(self):
        self.old_link.parent.mkdir(parents=True)
        self.old_link.symlink_to(self.home)
        quiet(brainrc.cmd_sync, True)
        self.assertTrue(self.old_link.is_symlink())
        self.assertEqual(brainrc.link_target(self.link), self.repo / "overrides/opencode/plugin.js")

    def test_disabling_the_harness_prunes_the_plugin(self):
        quiet(brainrc.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[opencode]\nenabled = false\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse(self.link.is_symlink())

    def test_validate_needs_the_plugin_file(self):
        (self.repo / "overrides/opencode/plugin.js").unlink()
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("overrides/opencode/plugin.js", out)


CURSOR_FRAGMENT = REPO / "overrides/cursor/settings.fragment.json"
CURSOR_FOREIGN = {"command": "node /opt/other/cursor-hook.js"}


class CursorHooksTest(TempRepoCase):
    """[cursor] merges guard hooks into ~/.cursor/hooks.json, whose entries are flat {command}s."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        self.hooks_json = self.home / ".cursor/hooks.json"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def wanted(self):
        m = brainrc.SettingsMerge("cursor", self.hooks_json, [(CURSOR_FRAGMENT, "~/.cursor/hooks/ai-config")])
        return m.wanted(), m.markers()

    def test_merge_keeps_foreign_entries_replaces_ours_and_is_idempotent(self):
        wanted, markers = self.wanted()
        old = {"command": "python3 ~/.cursor/hooks/ai-config/old.py"}
        current = {"version": 1, "hooks": {"beforeShellExecution": [CURSOR_FOREIGN, old]}}
        once = brainrc.merge_settings(current, wanted, markers)
        shell = once["hooks"]["beforeShellExecution"]
        self.assertEqual(shell[0], CURSOR_FOREIGN)
        self.assertNotIn(old, shell)
        self.assertIn(cursor_guard("$HOME/.cursor/hooks/ai-config"), [e["command"] for e in shell])
        self.assertIn("beforeReadFile", once["hooks"])
        self.assertEqual(brainrc.merge_settings(once, wanted, markers), once)

    def test_a_new_file_gets_version_1_and_a_users_version_is_kept(self):
        wanted, markers = self.wanted()
        self.assertEqual(brainrc.merge_settings({}, wanted, markers)["version"], 1)
        self.assertEqual(brainrc.merge_settings({"version": 2}, wanted, markers)["version"], 2)

    def test_claude_fragment_adds_no_top_level_keys(self):
        m = brainrc.SettingsMerge("claude", self.home / "s.json", [(FRAGMENT, "~/.claude/hooks/ai-config")])
        self.assertEqual(set(brainrc.merge_settings({}, m.wanted(), m.markers())), {"hooks"})

    def test_apply_writes_hooks_json_links_the_hooks_dir_and_doctor_is_clean(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        data = json.loads(self.hooks_json.read_text())
        self.assertEqual(data["version"], 1)
        self.assertEqual(brainrc.link_target(self.home / ".cursor/hooks/brainrc"),
                         self.repo / "overrides/cursor/hooks")
        self.assertEqual(brainrc.doctor_findings(), [])
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(json.loads(self.hooks_json.read_text()), data)


class CursorPluginTest(TempRepoCase):
    """.cursor-plugin/plugin.json: Cursor's manifest, generated like the others."""

    def manifest(self):
        return json.loads(brainrc.plugin_manifests()[".cursor-plugin/plugin.json"])

    def test_manifest_points_at_core_and_runs_the_cursor_guard(self):
        set_core_version(self.repo, "1.2.3")
        plugin = self.manifest()
        self.assertEqual((plugin["name"], plugin["version"], plugin["license"]), ("brainrc", "1.2.3", "MIT"))
        self.assertEqual((plugin["skills"], plugin["agents"], plugin["rules"]), ("./skills/", "./agents/", "./rules/"))
        self.assertEqual(plugin["hooks"], "./.cursor-plugin/hooks.json")
        hooks = json.loads(brainrc.plugin_manifests()[".cursor-plugin/hooks.json"])
        self.assertEqual(hooks["version"], 1)
        commands = [e["command"] for entries in hooks["hooks"].values() for e in entries]
        self.assertEqual(set(hooks["hooks"]), {"beforeShellExecution", "beforeReadFile"})
        self.assertTrue(all(c == cursor_guard("${CURSOR_PLUGIN_ROOT}/overrides/cursor/hooks")
                            for c in commands), commands)
        self.assertNotIn("..", json.dumps(plugin))

    def test_validate_reports_a_missing_cursor_manifest(self):
        quiet(brainrc.cmd_plugin)
        self.assertEqual(brainrc.check_plugin(), [])
        (self.repo / ".cursor-plugin/plugin.json").unlink()
        self.assertTrue(any(".cursor-plugin/plugin.json" in e and "missing" in e for e in brainrc.check_plugin()))

    def test_rules_need_always_apply(self):
        rule = self.repo / "rules/10-git.md"
        rule.write_text(rule.read_text().replace("alwaysApply: true\n", ""))
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("rules/10-git.md", out)
        self.assertIn("alwaysApply", out)


class PackValidateTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")

    def tearDown(self):
        shutil.rmtree(self.pack.parent)
        super().tearDown()

    def test_valid_pack(self):
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertIn("(packs: acme)", out)

    def test_catches_pack_errors(self):
        (self.pack / "pack.toml").write_text(PACK_TOML.replace('skills = ["acme-deploy"]', 'skills = ["nope"]')
                                             .replace('connector = "ticket-github"', 'connector = "ticket-ghost"'))
        (self.pack / "skills/unprefixed").mkdir()
        (self.pack / "skills/unprefixed/SKILL.md").write_text("---\nname: unprefixed\ndescription: x\n---\n")
        (self.pack / "tripwires.toml").write_text(
            '[[tripwire]]\nid = "T1"\npattern = "Acme rule"\nallow = "(?i)never"\nmessage = "stale rule"\n')
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        for expected in ("acme:skills/unprefixed: pack skills must start with `acme-`",
                         "domains names unknown skill `nope`",
                         "ticket.connector names unknown skill `ticket-ghost`",
                         "acme:rules/50-acme.md:3: tripwire T1: stale rule"):
            self.assertIn(expected, out)

    def test_compatible_pack_has_no_version_message(self):
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertNotIn("requires_core", out)

    def test_incompatible_pack_fails(self):
        set_requires_core(self.pack, 'requires_core = ">=1.3"')
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:pack.toml: requires_core `>=1.3` is not satisfied by core 1.2.3", out)

    def test_incompatible_enabled_pack_fails_plain_validate(self):
        set_requires_core(self.pack, 'requires_core = "<1"')
        (self.repo / "packs.local.toml").write_text(f'[acme]\npath = "{self.pack}"\n')
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("requires_core `<1` is not satisfied by core 1.2.3", out)

    def test_missing_requires_core_warns(self):
        set_requires_core(self.pack, "")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN acme:pack.toml: no `requires_core`", out)
        set_core_version(self.repo, "0.3.1")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertIn('requires_core = ">=0.3, <0.4"', out)  # 0.x: breaking changes bump MINOR

    def test_malformed_requires_core_fails(self):
        set_requires_core(self.pack, 'requires_core = "latest"')
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:pack.toml: invalid requires_core `latest`", out)
        self.assertIn('">=0.1, <0.2"', out)  # shows the accepted syntax

    def test_invalid_core_version_fails(self):
        (self.repo / "VERSION").write_text("one\n")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("VERSION: `one` is not MAJOR.MINOR.PATCH", out)

    def test_tripwire_allow_pattern_passes_line(self):
        (self.pack / "rules/50-acme.md").write_text("- Never use the old Acme rule.\n")
        (self.pack / "tripwires.toml").write_text(
            '[[tripwire]]\nid = "T1"\npattern = "Acme rule"\nallow = "(?i)never"\n')
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)


class ChangelogCheckTest(TempRepoCase):
    """validate keeps VERSION and the newest CHANGELOG entry in step, with no Unreleased section."""

    def setUp(self):
        super().setUp()
        set_core_version(self.repo, "1.2.3")

    def test_matching_changelog_passes(self):
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_version_without_changelog_entry_fails(self):
        (self.repo / "VERSION").write_text("1.2.4\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md: newest version 1.2.3 doesn't match VERSION 1.2.4", out)

    def test_unreleased_section_fails(self):
        (self.repo / "CHANGELOG.md").write_text(
            "# Changelog\n\n## Unreleased\n\n- New.\n\n## 1.2.3 (2026-01-01)\n\n- Change.\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md: has an `## Unreleased` section", out)

    def test_changelog_without_version_heading_fails(self):
        (self.repo / "CHANGELOG.md").write_text("# Changelog\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md: no `## X.Y.Z` heading", out)


def write_skill(root: Path, name: str, body: str) -> None:
    (root / "skills" / name).mkdir(parents=True, exist_ok=True)
    (root / "skills" / name / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Test connector {name}.\n---\n# {name}\n\n{body}")


class ConnectorCheckTest(TempRepoCase):
    """Connector skills need a heading for every required operation (references/connectors.md)."""

    def setUp(self):
        super().setUp()
        set_core_version(self.repo, "1.2.3")

    def test_core_connectors_pass(self):
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_core_connector_missing_an_operation_fails(self):
        write_skill(self.repo, "ticket-x", "## fetch\n\n## comment\n\n## transition\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("skills/ticket-x/SKILL.md: connector missing `##` sections for link_pr", out)

    def test_core_local_and_github_connectors_document_create(self):
        for name in ("ticket-local", "ticket-github"):
            text = (Path(__file__).resolve().parent.parent / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, r"(?m)^## create\b", name)

    def test_a_connector_without_create_still_validates(self):
        write_skill(self.repo, "ticket-w", "## fetch\n\n## comment / transition / link_pr\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_one_heading_may_name_several_operations(self):
        write_skill(self.repo, "ticket-y", "## fetch (read-only)\n\n## comment / transition / link_pr\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_pr_status_is_optional_for_connectors(self):
        write_skill(self.repo, "ticket-with", "## fetch\n\n## comment / transition / link_pr\n\n## pr_status\n")
        write_skill(self.repo, "ticket-without", "## fetch\n\n## comment / transition / link_pr\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertNotIn("pr_status", out)

    def test_pr_status_does_not_replace_required_operations(self):
        write_skill(self.repo, "ticket-z", "## fetch\n\n## comment / transition\n\n## pr_status\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("skills/ticket-z/SKILL.md: connector missing `##` sections for link_pr", out)

    def test_pack_connector_missing_operations_fails(self):
        pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack",
                         PACK_TOML.replace('connector = "ticket-github"', 'connector = "acme-tickets"'))
        self.addCleanup(shutil.rmtree, pack.parent)
        write_skill(pack, "acme-tickets", "## fetch\n")
        code, out = quiet(brainrc.cmd_validate, str(pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:skills/acme-tickets/SKILL.md: connector missing `##` sections for "
                      "comment, transition, link_pr", out)


class ExamplePackTest(unittest.TestCase):
    """examples/pack-acme is the copyable template: it must pass against the real core VERSION."""

    def test_example_pack_is_valid_without_warnings(self):
        code, out = quiet(brainrc.cmd_validate, str(REPO / "examples/pack-acme"))
        self.assertEqual(code, 0, out)
        self.assertNotIn("WARN", out)
        self.assertIn("(packs: acme)", out)


class ValidateTest(unittest.TestCase):
    def test_repo_is_valid(self):
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_catches_placeholder_without_hooks_dir(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            copy_repo(tmp)
            toml = tmp / "harnesses.toml"
            toml.write_text(toml.read_text().replace('hooks_dir = "~/.claude/hooks/brainrc"\n', ""))
            old = brainrc.config.REPO
            brainrc.config.REPO = tmp
            try:
                code, out = quiet(brainrc.cmd_validate)
            finally:
                brainrc.config.REPO = old
            self.assertEqual(code, 1)
            self.assertIn("has no hooks_dir", out)
        finally:
            shutil.rmtree(tmp)

    def test_catches_broken_references(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            copy_repo(tmp)
            skill = tmp / "skills/spec-agent/SKILL.md"
            skill.write_text(skill.read_text() + "\n[agent: ghost] [x](missing.md) the `nope` skill\n")
            (tmp / "agents/verifier.md").write_text(
                (tmp / "agents/verifier.md").read_text().replace("model: haiku", "model: gpt-9"))
            old = brainrc.config.REPO
            brainrc.config.REPO = tmp
            try:
                code, out = quiet(brainrc.cmd_validate)
            finally:
                brainrc.config.REPO = old
            self.assertEqual(code, 1)
            for expected in ("unknown agent `ghost`", "broken link `missing.md`",
                             "unknown skill `nope`", "unknown model `gpt-9`"):
                self.assertIn(expected, out)
        finally:
            shutil.rmtree(tmp)


class ConfigErrorTest(TempRepoCase):
    """Bad harness and pack config: `ERROR <file>:<line>: <what>`, exit 1, nothing written."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def assert_error(self, error: str) -> None:
        """status, apply, and validate print the error and exit 1; apply writes nothing; doctor
        reports it as a FAIL."""
        for fn, args in ((brainrc.cmd_sync, (False,)), (brainrc.cmd_sync, (True,)), (brainrc.cmd_validate, ())):
            code, out = quiet(fn, *args)
            self.assertEqual(code, 1, out)
            self.assertIn(f"ERROR {error}", out)
        self.assertEqual(list(self.home.iterdir()), [])
        fails = [f[1] for f in brainrc.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any(error in f for f in fails), fails)
        code, _ = quiet(brainrc.cmd_doctor)
        self.assertEqual(code, 1)

    def local(self, name: str, text: str) -> str:
        (self.repo / f"{name}.local.toml").write_text(text)
        return brainrc.tilde(self.repo / f"{name}.local.toml")

    def test_toml_syntax_error_names_file_and_line(self):
        path = self.local("harnesses", "[claude]\nenabled = false\nskills = \n")
        self.assert_error(f"{path}:3: invalid TOML: Invalid value")

    def test_toml_syntax_error_at_end_of_document(self):
        path = self.local("packs", '[acme]\npath = "unterminated')  # no final newline
        self.assert_error(f"{path}:2: invalid TOML: Unterminated string")

    def test_syntax_error_in_shipped_file(self):
        (self.repo / "harnesses.toml").write_text("[claude\n")
        self.assert_error(f"{brainrc.tilde(self.repo / 'harnesses.toml')}:1: invalid TOML")

    def test_top_level_value_needs_a_table(self):
        path = self.local("harnesses", "# off here\nclaude = false\n")
        self.assert_error(f"{path}:2: `claude` must be a table, e.g. [claude]")

    def test_enabled_must_be_a_boolean(self):
        path = self.local("harnesses", '[codex]\nskills = "~/x"\nenabled = "false"\n')
        self.assert_error(f"{path}:3: [codex] `enabled` must be true or false")

    def test_pack_enabled_must_be_a_boolean(self):
        path = self.local("packs", '[acme]\npath = "/x"\nenabled = 0\n')
        self.assert_error(f"{path}:3: [acme] `enabled` must be true or false")

    def test_path_keys_must_be_strings(self):
        path = self.local("harnesses", "[claude]\nskills = 3\n")
        self.assert_error(f"{path}:2: [claude] `skills` must be a string")
        (self.repo / "harnesses.local.toml").unlink()
        path = self.local("packs", "[acme]\npath = [\"/x\"]\n")
        self.assert_error(f"{path}:2: [acme] `path` must be a string")

    def test_inline_table_value_points_at_its_line(self):
        path = self.local("harnesses", '\nclaude = { enabled = "no" }\n')
        self.assert_error(f"{path}:2: [claude] `enabled` must be true or false")


    def assert_warning(self, warning: str) -> None:
        """status, apply, and validate print the warning once and carry on; doctor reports it."""
        for fn, args in ((brainrc.cmd_sync, (False,)), (brainrc.cmd_sync, (True,)), (brainrc.cmd_validate, ())):
            code, out = quiet(fn, *args)
            self.assertEqual(code, 0, out)
            self.assertEqual(out.count(f"WARN {warning}"), 1, out)
        warns = [f[1] for f in brainrc.doctor_findings() if f[0] == "WARN"]
        self.assertIn(warning, warns)

    def test_unknown_harness_key_warns(self):
        path = self.local("harnesses", "[claude]\nenabeld = false\n")
        self.assert_warning(f"{path}:2: unknown key `enabeld` in [claude]")

    def test_unknown_pack_key_warns(self):
        pack = self.repo / "packs-src/acme"
        (pack / "skills").mkdir(parents=True)
        (pack / "pack.toml").write_text('name = "acme"\nrequires_core = ">=0.1"\n')
        path = self.local("packs", f'[acme]\npath = "{pack}"\nreff = "v1"\n')
        self.assert_warning(f"{path}:3: unknown key `reff` in [acme]")

    def test_harness_only_in_local_file_warns_and_still_loads(self):
        path = self.local("harnesses", '[cursr]\nskills = "~/.cursr/skills"\n')
        self.assert_warning(f"{path}:1: unknown harness [cursr]")
        self.assertTrue((self.home / ".cursr/skills/spec-agent").is_symlink())

    def test_shipped_config_is_quiet(self):
        for fn, args in ((brainrc.cmd_sync, (False,)), (brainrc.cmd_validate, ())):
            code, out = quiet(fn, *args)
            self.assertEqual(code, 0, out)
            self.assertNotIn("WARN", out)
            self.assertNotIn("ERROR", out)


    def pack(self, text: str) -> str:
        pack = self.repo / "packs-src/acme"
        (pack / "skills").mkdir(parents=True, exist_ok=True)
        (pack / "pack.toml").write_text(text)
        self.local("packs", f'[acme]\npath = "{pack}"\n')
        return brainrc.tilde(pack / "pack.toml")

    def test_pack_toml_syntax_error_names_file_and_line(self):
        path = self.pack('name = "acme"\nprefix = acme-\n')
        self.assert_error(f"{path}:2: invalid TOML: Invalid value")
        code, out = quiet(brainrc.cmd_validate, str(self.repo / "packs-src/acme"))
        self.assertEqual(code, 1, out)
        self.assertIn(f"ERROR {path}:2: invalid TOML", out)

    def test_pack_name_and_prefix_must_be_strings(self):
        path = self.pack('requires_core = ">=0.1"\nname = 7\n')
        self.assert_error(f"{path}:2: `name` must be a string")
        path = self.pack('name = "acme"\nprefix = false\n')
        self.assert_error(f"{path}:2: `prefix` must be a string")


class ClosedStdoutTest(unittest.TestCase):
    """`brainrc doctor | head -1`: the reader stops early, brainrc exits quietly."""

    def test_closed_stdout_exits_without_a_traceback(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        env = {**os.environ, "HOME": str(tmp), "BRAINRC_HOME": str(tmp / "brainrc")}
        for cmd in ("doctor", "status"):
            p = subprocess.Popen([sys.executable, str(REPO / "scripts/brainrc.py"), cmd], env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.stdout.close()  # nobody reads: every write gets EPIPE
            _, err = p.communicate(timeout=60)
            self.assertNotIn(b"Traceback", err, cmd)
            self.assertNotIn(b"BrokenPipe", err, cmd)
            self.assertEqual(p.returncode, 0, (cmd, err))


class DuplicatePackTest(TempRepoCase):
    """Two enabled packs with one name share a hooks dir and fight on every apply."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def packs(self, **names: str) -> None:
        """One pack per key, each with the given pack.toml name."""
        lines = []
        for key, name in names.items():
            root = self.repo / "packs-src" / key
            (root / "skills").mkdir(parents=True)
            (root / "pack.toml").write_text(f'name = "{name}"\nrequires_core = ">=0.1"\n')
            lines.append(f'[{key}]\npath = "{root}"\n')
        (self.repo / "packs.local.toml").write_text("".join(lines))

    def test_two_packs_with_one_name_are_refused(self):
        self.packs(one="acme", two="acme")
        error = "ERROR pack name `acme` is used by both [one] and [two]"
        for fn, args in ((brainrc.cmd_validate, ()), (brainrc.cmd_sync, (False,)), (brainrc.cmd_sync, (True,))):
            code, out = quiet(fn, *args)
            self.assertEqual(code, 1, out)
            self.assertIn(error, out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_doctor_reports_duplicate_names(self):
        self.packs(one="acme", two="acme")
        fails = [f for f in brainrc.doctor_findings() if f[0] == "FAIL" and "is used by both" in f[1]]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("[one] and [two]", fails[0][1])
        self.assertIn("enabled = false", fails[0][2])
        self.assertIn("pack.toml", fails[0][2])
        code, _ = quiet(brainrc.cmd_doctor)
        self.assertEqual(code, 1)

    def test_a_pack_named_core_is_refused(self):
        self.packs(two="core")
        for fn, args in ((brainrc.cmd_validate, ()), (brainrc.cmd_sync, (True,))):
            code, out = quiet(fn, *args)
            self.assertEqual(code, 1, out)
            self.assertIn("ERROR pack name `core` is used by both core and [two]", out)
        code, out = quiet(brainrc.cmd_validate, str(self.repo / "packs-src/two"))
        self.assertEqual(code, 1, out)
        self.assertIn(f"used by both core and {brainrc.tilde(self.repo / 'packs-src/two')}", out)

    def test_key_and_name_may_differ(self):
        self.packs(work="acme")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertNotIn("is used by both", out)


class PackApplyCheckTest(TempRepoCase):
    """apply and status run validate --pack's checks on each enabled pack before linking."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        self.pack = self.repo / "packs-src/acme"
        (self.pack / "skills").mkdir(parents=True)
        (self.pack / "pack.toml").write_text('name = "acme"\nrequires_core = ">=0.1"\n')
        (self.repo / "packs.local.toml").write_text(f'[acme]\npath = "{self.pack}"\n')

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def skill(self, name: str, description: str = "Deploy things. Use when deploying.") -> None:
        (self.pack / "skills" / name).mkdir()
        meta = f"description: {description}\n" if description else ""
        (self.pack / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\n{meta}---\nBody\n")

    def assert_refused(self, error: str) -> None:
        for apply in (False, True):
            code, out = quiet(brainrc.cmd_sync, apply)
            self.assertEqual(code, 1, out)
            self.assertIn(f"ERROR {error}", out)
            self.assertIn(f"validate --pack {brainrc.tilde(self.pack)}", out)
            self.assertIn("Nothing written", out)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse(self.settings_home.joinpath("instructions.md").exists())

    def test_unprefixed_skill_is_refused(self):
        self.skill("deploy")
        self.assert_refused("acme:skills/deploy: pack skills must start with `acme-`")

    def test_any_pack_validate_error_is_refused(self):
        self.skill("acme-deploy", description="")
        self.assert_refused("acme:skills/acme-deploy/SKILL.md: missing `description`")

    def test_only_the_failing_pack_is_named(self):
        self.skill("deploy")
        good = self.repo / "packs-src/good"
        (good / "skills").mkdir(parents=True)
        (good / "pack.toml").write_text('name = "good"\nrequires_core = ">=0.1"\n')
        with open(self.repo / "packs.local.toml", "a") as f:
            f.write(f'[good]\npath = "{good}"\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertNotIn(f"validate --pack {brainrc.tilde(good)}", out)

    def test_a_valid_pack_links_as_before(self):
        self.skill("acme-deploy")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("ERROR", out)
        self.assertTrue((self.home / ".claude/skills/acme-deploy").is_symlink())


class AgentFrontmatterTest(TempRepoCase):
    """Agent `model` and `tools` names validate accepts."""

    def agent(self, model: str, tools: str) -> tuple[int, str]:
        path = self.repo / "agents/verifier.md"
        text = path.read_text()
        head, sep, body = text.partition("\n---\n")
        lines = [l for l in head.splitlines() if not l.startswith(("model:", "tools:"))]
        path.write_text("\n".join(lines + [f"model: {model}", f"tools: {tools}"]) + sep + body)
        return quiet(brainrc.cmd_validate)

    def test_full_claude_model_id_is_accepted(self):
        for model in ("claude-sonnet-5-5", "claude-opus-4-1-20250805", "claude-3.5-haiku"):
            code, out = self.agent(model, "Read")
            self.assertNotIn("unknown model", out, model)
            self.assertEqual(code, 0, out)

    def test_task_tool_is_accepted(self):
        code, out = self.agent("haiku", "Read, Task")
        self.assertNotIn("unknown tool", out)
        self.assertEqual(code, 0, out)

    def test_unknown_names_still_fail(self):
        for model, tools, error in (("gpt-9", "Read", "unknown model `gpt-9`"),
                                    ("claude-", "Read", "unknown model `claude-`"),
                                    ("Claude-Sonnet", "Read", "unknown model `Claude-Sonnet`"),
                                    ("haiku", "Read, Nope", "unknown tool `Nope`")):
            code, out = self.agent(model, tools)
            self.assertEqual(code, 1, out)
            self.assertIn(error, out)


class BrainrcCommandTest(unittest.TestCase):
    """The package and command are named brainrc (#205)."""

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(REPO / "scripts/brainrc.py"), *args],
                              capture_output=True, text=True)

    def test_version_prints_name_and_version_without_v(self):
        result = self.run_script("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"brainrc {(REPO / 'VERSION').read_text().strip()}\n")

    def test_usage_names_brainrc_in_a_checkout(self):
        for arg in ("help", "bogus"):
            result = self.run_script(arg)
            self.assertEqual(result.returncode, 2)
            self.assertIn("brainrc.py status", result.stdout)
            self.assertNotIn("aicfg.py", result.stdout)

    def test_usage_names_brainrc_when_installed(self):
        with mock.patch("brainrc.config.installed", return_value=True):
            code, out = quiet(brainrc.cli.main, ["brainrc", "bogus"])
        self.assertEqual(code, 2)
        self.assertIn("brainrc status", out)
        self.assertNotIn("brainrc.py", out)
        self.assertNotIn("aicfg", out.replace("AICFG_HOME", ""))

    def test_checkout_script_validates(self):
        self.assertEqual(self.run_script("validate").returncode, 0)


class PyprojectTest(unittest.TestCase):
    def setUp(self):
        import tomllib
        self.data = tomllib.loads((REPO / "pyproject.toml").read_text())

    def test_distribution_and_console_scripts(self):
        self.assertEqual(self.data["project"]["name"], "brainrc")
        scripts = self.data["project"]["scripts"]
        self.assertEqual(scripts["brainrc"], "brainrc.cli:entry")
        self.assertEqual(list(scripts), ["brainrc"])
        self.assertEqual(self.data["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"], ["brainrc"])
        self.assertIn("brainrc", self.data["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"])

    def test_bundled_core_lands_under_brainrc(self):
        include = self.data["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
        self.assertTrue(include)
        for src, dest in include.items():
            self.assertTrue((REPO / src).exists(), src)
            self.assertTrue(dest.startswith("brainrc/_core/"), dest)
        for needed in ("skills", "agents", "rules", "harnesses.toml", "VERSION", "CHANGELOG.md"):
            self.assertIn(needed, include)


if __name__ == "__main__":
    unittest.main()
