"""Tests for scripts/aicfg.py: settings merge, sync against a fake HOME, and validation."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import aicfg  # noqa: E402  (the package at the repo root)

FOREIGN = {"hooks": [{"type": "command", "command": "node /opt/other/hook.js"}]}
OURS_OLD = {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/ai-config/old.py"}]}
SOURCES = ("skills", "agents", "overrides", "rules")  # core ships no commands/ (packs may)
FRAGMENT = REPO / "overrides/claude/settings.fragment.json"


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
    """Point aicfg at a throwaway copy of the repo and AICFG_HOME, so tests never read local
    config or write rendered files anywhere real."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        copy_repo(self.repo)
        self.old_repo = aicfg.config.REPO
        aicfg.config.REPO = self.repo
        self.aicfg_home = Path(tempfile.mkdtemp()) / "ai-config"
        self.old_aicfg_home = os.environ.get("AICFG_HOME")
        os.environ["AICFG_HOME"] = str(self.aicfg_home)

    def tearDown(self):
        aicfg.config.REPO = self.old_repo
        if self.old_aicfg_home is None:
            os.environ.pop("AICFG_HOME", None)
        else:
            os.environ["AICFG_HOME"] = self.old_aicfg_home
        shutil.rmtree(self.aicfg_home.parent)
        shutil.rmtree(self.repo)


class MergeSettingsTest(unittest.TestCase):
    def setUp(self):
        self.fragment = aicfg.render_fragment(FRAGMENT, "~/.claude/hooks/ai-config")

    def test_renders_hooks_dir_placeholder(self):
        commands = [h["command"] for g in self.fragment["hooks"]["PreToolUse"] for h in g["hooks"]]
        self.assertIn('python3 "$HOME/.claude/hooks/ai-config/guard_outward.py"', commands)
        self.assertFalse(any(aicfg.HOOKS_DIR_PLACEHOLDER in c for c in commands))

    def test_custom_hooks_dir_is_owned(self):
        m = aicfg.SettingsMerge("claude", Path("unused"), [(FRAGMENT, "/opt/hooks/mine")])
        once = aicfg.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, m.wanted(), m.markers())
        self.assertEqual(aicfg.merge_settings(once, m.wanted(), m.markers()), once)
        self.assertIn("/opt/hooks/mine/guard_outward.py", json.dumps(once))

    def test_preserves_foreign_hooks_and_other_keys(self):
        current = {"tui": "fullscreen", "hooks": {"SessionStart": [FOREIGN], "PreToolUse": [FOREIGN]}}
        merged = aicfg.merge_settings(current, self.fragment)
        self.assertEqual(merged["tui"], "fullscreen")
        self.assertEqual(merged["hooks"]["SessionStart"], [FOREIGN])
        self.assertEqual(merged["hooks"]["PreToolUse"][0], FOREIGN)
        self.assertEqual(len(merged["hooks"]["PreToolUse"]), 1 + len(self.fragment["hooks"]["PreToolUse"]))

    def test_idempotent(self):
        once = aicfg.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, self.fragment)
        self.assertEqual(aicfg.merge_settings(once, self.fragment), once)

    def test_replaces_stale_owned_groups(self):
        merged = aicfg.merge_settings({"hooks": {"PostToolUse": [OURS_OLD]}}, self.fragment)
        self.assertNotIn("PostToolUse", merged["hooks"])
        self.assertNotIn(OURS_OLD, merged["hooks"]["PreToolUse"])

    def test_does_not_mutate_input(self):
        current = {"hooks": {"PreToolUse": [FOREIGN]}}
        aicfg.merge_settings(current, self.fragment)
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
        code, out = quiet(aicfg.cmd_sync, False)
        self.assertEqual(code, 0)
        self.assertIn("Dry run", out)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse((self.repo / "dist").exists())
        self.assertFalse(self.aicfg_home.exists())

    def test_relative_symlink_into_repo_is_ok(self):
        quiet(aicfg.cmd_sync, True)
        link = self.home / ".claude/skills/spec-agent"
        link.unlink()
        link.symlink_to(os.path.relpath(self.repo / "skills/spec-agent", link.parent))
        self.assertEqual(aicfg.Link("claude", link, self.repo / "skills/spec-agent").state(), "ok")

    def test_updates_moved_links_and_prunes_dangling(self):
        quiet(aicfg.cmd_sync, True)
        skills_dir = self.home / ".claude/skills"
        (skills_dir / "spec-agent").unlink()
        (skills_dir / "spec-agent").symlink_to(self.repo / "skills/terraform")  # points at wrong skill
        (skills_dir / "gone").symlink_to(self.repo / "skills/gone")  # removed from the repo
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0)
        self.assertIn("UPDATE", out)
        self.assertIn("PRUNE", out)
        self.assertEqual(aicfg.link_target(skills_dir / "spec-agent"), self.repo / "skills/spec-agent")
        self.assertFalse((skills_dir / "gone").is_symlink())

    def test_invalid_settings_json_is_a_conflict(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        settings.write_text("{ not json")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1)
        self.assertIn("invalid JSON", out)
        self.assertEqual(settings.read_text(), "{ not json")

    def test_disabling_harness_removes_only_its_owned_hooks(self):
        quiet(aicfg.cmd_sync, True)
        settings = self.home / ".claude/settings.json"
        data = json.loads(settings.read_text())
        data["tui"] = "fullscreen"
        data["hooks"]["PreToolUse"].insert(0, FOREIGN)
        settings.write_text(json.dumps(data))
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        before = settings.read_text()

        code, out = quiet(aicfg.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"MERGE +claude +~/.claude/settings.json")
        self.assertEqual(settings.read_text(), before)

        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        after = json.loads(settings.read_text())
        self.assertNotIn("hooks/ai-config", json.dumps(after))
        self.assertEqual(after["hooks"]["PreToolUse"], [FOREIGN])
        self.assertEqual(after["tui"], "fullscreen")
        self.assertTrue(list(settings.parent.glob("settings.json.bak-aicfg-*")))
        self.assertIn("Everything in sync.", quiet(aicfg.cmd_sync, False)[1])

    def test_uninstall_restores_the_settings_file(self):
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text('{"theme": "dark"}\n')
        quiet(aicfg.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        quiet(aicfg.cmd_sync, True)
        self.assertEqual(json.loads(settings.read_text()), {"theme": "dark"})

    def test_disabled_harness_without_settings_is_left_alone(self):
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".claude/settings.json").exists())

    def test_backups_are_capped(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        for n in range(aicfg.BACKUPS_KEPT + 3):
            (settings.parent / f"settings.json.bak-aicfg-2026010{n}T000000Z").write_text("{}")
        settings.write_text("{}")
        quiet(aicfg.cmd_sync, True)
        self.assertEqual(len(list(settings.parent.glob("settings.json.bak-aicfg-*"))), aicfg.BACKUPS_KEPT)
        self.assertEqual(list(settings.parent.glob(".settings.json.aicfg-tmp")), [])

    def test_apply_then_in_sync_and_conflicts_respected(self):
        (self.home / ".claude").mkdir()
        settings = self.home / ".claude/settings.json"
        settings.write_text(json.dumps({"hooks": {"SessionStart": [FOREIGN]}}))
        (self.home / ".codex").mkdir()
        (self.home / ".codex/AGENTS.md").write_text("mine\n")

        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1)  # the pre-existing codex file is a conflict
        self.assertIn("CONFLICT", out)
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text(), "mine\n")

        skill = self.home / ".claude/skills/spec-agent"
        self.assertTrue(skill.is_symlink())
        self.assertTrue((skill / "roles" / "implementer.md").is_file())
        self.assertTrue((self.home / ".claude/hooks/ai-config/guard_outward.py").is_file())

        merged = json.loads(settings.read_text())
        self.assertEqual(merged["hooks"]["SessionStart"], [FOREIGN])
        self.assertTrue(any(aicfg._owned(g) for g in merged["hooks"]["PreToolUse"]))
        self.assertEqual(len(list(settings.parent.glob("settings.json.bak-aicfg-*"))), 1)

        (self.home / ".codex/AGENTS.md").unlink()
        quiet(aicfg.cmd_sync, True)
        code, out = quiet(aicfg.cmd_sync, False)
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
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        skills_dir = self.home / ".claude/skills"
        self.assertEqual(aicfg.link_target(skills_dir / "acme-deploy"), self.pack / "skills/acme-deploy")
        self.assertTrue((skills_dir / "spec-agent").is_symlink())
        self.assertTrue((self.home / ".claude/agents/acme-reviewer.md").is_symlink())

        rules = aicfg.rendered_instructions().read_text()
        self.assertLess(rules.index("# Security"), rules.index("- Acme rule."))

        hooks_link = self.home / ".claude/hooks/ai-config-acme"
        self.assertEqual(aicfg.link_target(hooks_link), self.pack / "overrides/claude/hooks")
        commands = self.settings_commands()
        self.assertIn('python3 "$HOME/.claude/hooks/ai-config/guard_outward.py"', commands)
        self.assertIn('python3 "$HOME/.claude/hooks/ai-config-acme/guard_acme.py"', commands)

        ext = aicfg.extensions_file().read_text()
        for expected in ("| `deploy/*.yaml` | acme-deploy | infra-reviewer | acme |",
                         "- `acme-context` (acme): every ticket", '"connector": "ticket-github"',
                         "- (acme) Deploy plan reviewed"):
            self.assertIn(expected, ext)

        code, out = quiet(aicfg.cmd_sync, False)
        self.assertEqual((code, out.strip()), (0, "Everything in sync."))

    def test_disabling_pack_removes_its_links_and_hooks(self):
        quiet(aicfg.cmd_sync, True)
        self.enable_pack(False)
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".claude/skills/acme-deploy").is_symlink())
        self.assertFalse((self.home / ".claude/agents/acme-reviewer.md").is_symlink())
        self.assertFalse((self.home / ".claude/hooks/ai-config-acme").is_symlink())
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())
        commands = self.settings_commands()
        self.assertFalse(any("guard_acme" in c for c in commands))
        self.assertTrue(any("guard_outward" in c for c in commands))
        self.assertNotIn("- Acme rule.", aicfg.rendered_instructions().read_text())
        self.assertIn("No packs enabled", aicfg.extensions_file().read_text())

    def test_disabling_harness_prunes_its_links(self):
        quiet(aicfg.cmd_sync, True)
        self.assertTrue((self.home / ".cursor/skills/spec-agent").is_symlink())
        (self.repo / "harnesses.local.toml").write_text("[cursor]\nenabled = false\n")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(list((self.home / ".cursor/skills").iterdir()), [])

    def test_name_collision_writes_nothing(self):
        clash = self.pack / "skills/spec-agent"
        clash.mkdir()
        (clash / "SKILL.md").write_text("---\nname: spec-agent\ndescription: Clash.\n---\n")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1)
        self.assertIn("skill `spec-agent` is defined in both core and acme", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_pack_is_an_error(self):
        (self.repo / "packs.local.toml").write_text('[ghost]\npath = "/nonexistent/pack"\n')
        code, out = quiet(aicfg.cmd_sync, False)
        self.assertEqual(code, 1)
        self.assertIn("no pack.toml", out)

    def set_requires_core(self, line: str) -> None:
        set_requires_core(self.pack, line)

    def test_incompatible_pack_writes_nothing(self):
        self.set_requires_core('requires_core = ">=2.0"')
        for apply in (False, True):
            code, out = quiet(aicfg.cmd_sync, apply)
            self.assertEqual(code, 1, out)
            self.assertIn("acme:pack.toml: requires_core `>=2.0` is not satisfied by core 1.2.3", out)
            self.assertIn("Nothing written", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_disabled_incompatible_pack_is_not_checked(self):
        self.set_requires_core('requires_core = ">=2.0"')
        self.enable_pack(False)
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("requires_core", out)

    def test_pack_without_requires_core_applies_with_warning(self):
        self.set_requires_core("")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn("WARN acme:pack.toml: no `requires_core`", out)
        self.assertIn('requires_core = ">=1.2, <2"', out)  # suggests the documented pin
        self.assertTrue((self.home / ".claude/skills/acme-deploy").is_symlink())

    def test_tokens_lists_pack_items(self):
        code, out = quiet(aicfg.cmd_tokens)
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
        quiet(aicfg.cmd_sync, True)
        self.skills = self.home / ".claude/skills"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def doctor(self, expect_code: int | None = None) -> list[tuple[str, str, str]]:
        code, out = quiet(aicfg.cmd_doctor)
        if expect_code is not None:
            self.assertEqual(code, expect_code, out)
        return aicfg.doctor_findings()

    def assert_one_fail(self, what: str, fix: str) -> None:
        findings = self.doctor(1)
        fails = [f for f in findings if f[0] == "FAIL"]
        self.assertEqual(len(fails), 1, findings)
        self.assertIn(what, fails[0][1])
        self.assertIn(fix, fails[0][2])

    def test_clean_after_apply(self):
        code, out = quiet(aicfg.cmd_doctor)
        self.assertEqual(code, 0, out)
        self.assertIn("No problems found.", out)

    def test_points_to_troubleshooting_only_when_something_is_wrong(self):
        _, clean = quiet(aicfg.cmd_doctor)
        self.assertNotIn("troubleshooting", clean)
        (self.skills / "spec-agent").unlink()
        _, out = quiet(aicfg.cmd_doctor)
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
        aicfg.rendered_instructions().unlink()
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
        quiet(aicfg.cmd_sync, True)
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
        self.core = aicfg.Source("core", self.repo)
        self.old_budget = aicfg.tokens.CORE_ALWAYS_BUDGET

    def tearDown(self):
        aicfg.tokens.CORE_ALWAYS_BUDGET = self.old_budget
        shutil.rmtree(self.pack.parent)
        super().tearDown()

    def check(self, *packs):
        return aicfg.check_budgets([self.core, *packs])

    def test_core_is_within_budget_with_no_warnings(self):
        total, items = aicfg.always_tokens(self.core)
        self.assertGreater(total, 1000)
        self.assertLessEqual(total, aicfg.tokens.CORE_ALWAYS_BUDGET)
        self.assertEqual(self.check(), ([], []))

    def test_always_tokens_counts_rules_and_descriptions(self):
        total, items = aicfg.always_tokens(self.core)
        labels = [label for _, label in items]
        self.assertIn("rules/30-guardrails.md", labels)
        self.assertIn("skills/spec-agent", labels)
        self.assertIn("agents/verifier.md", labels)
        self.assertIn("skills/work", labels)
        self.assertEqual(total, sum(n for n, _ in items))

    def test_core_over_budget_fails_naming_the_biggest_items(self):
        aicfg.tokens.CORE_ALWAYS_BUDGET = 100
        errors, _ = self.check()
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("core", errors[0])
        self.assertIn("budget 100", errors[0])
        _, items = aicfg.always_tokens(self.core)
        for _, label in sorted(items, reverse=True)[:3]:
            self.assertIn(label, errors[0])
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("budget 100", out)

    def test_pack_over_its_declared_budget_fails(self):
        toml = self.pack / "pack.toml"
        toml.write_text(toml.read_text().replace('prefix = "acme-"\n', 'prefix = "acme-"\nmax_always_tokens = 10\n'))
        errors, _ = self.check(aicfg.load_pack(self.pack))
        self.assertTrue(any("acme" in e and "budget 10" in e for e in errors), errors)

    def test_pack_without_a_budget_warns_above_the_default(self):
        (self.pack / "rules/50-acme.md").write_text("# Acme\n\n" + "- Rule text here.\n" * 300)
        errors, warnings = self.check(aicfg.load_pack(self.pack))
        self.assertEqual(errors, [])
        self.assertTrue(any("acme" in w and "max_always_tokens" in w for w in warnings), warnings)

    def test_long_description_warns(self):
        skill = self.pack / "skills/acme-deploy/SKILL.md"
        skill.write_text("---\nname: acme-deploy\ndescription: " + "word " * 120 + "\n---\nBody.\n")
        _, warnings = self.check(aicfg.load_pack(self.pack))
        self.assertTrue(any("acme:skills/acme-deploy" in w and "description" in w for w in warnings), warnings)

    def test_tokens_shows_budget_per_source(self):
        code, out = quiet(aicfg.cmd_tokens)
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
        description = aicfg.frontmatter(self.SKILL / "SKILL.md")["description"]
        self.assertLessEqual(aicfg.estimate_tokens(description), 60)


class RolesLinkTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.roles = self.repo / "skills/spec-agent/roles"

    def assert_validate_fails(self):
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("skills/spec-agent/roles", out)
        self.assertIn("Platforms", out)

    def test_repo_link_passes(self):
        self.assertTrue(self.roles.is_symlink())
        self.assertIsNone(aicfg.check_roles_link())

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
        return json.loads(aicfg.plugin_manifests()[f".claude-plugin/{name}"])

    def test_plugin_manifest_comes_from_the_repo(self):
        set_core_version(self.repo, "1.2.3")
        plugin = self.manifest()
        self.assertEqual((plugin["name"], plugin["version"]), ("ai-config", "1.2.3"))
        self.assertEqual(plugin["author"], {"name": "ai-config contributors"})
        commands = [h["command"] for groups in plugin["hooks"].values() for g in groups for h in g["hooks"]]
        self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/overrides/claude/hooks/guard_outward.py"', commands)
        self.assertNotIn("{{hooks_dir}}", json.dumps(plugin))

    def test_antigravity_manifest_is_the_name_only(self):
        self.assertEqual(json.loads(aicfg.plugin_manifests()["plugin.json"]), {"name": "ai-config"})

    def test_marketplace_lists_the_repo_as_the_plugin(self):
        market = self.manifest("marketplace.json")
        self.assertEqual(market["name"], "ai-config")
        self.assertEqual(market["plugins"][0]["source"], ".")
        self.assertEqual(market["plugins"][0]["version"], self.manifest()["version"])

    def test_plugin_command_writes_once(self):
        code, out = quiet(aicfg.cmd_plugin)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.repo / ".claude-plugin/plugin.json").is_file())
        self.assertTrue((self.repo / "plugin.json").is_file())
        self.assertEqual(aicfg.check_plugin(), [])
        code, out = quiet(aicfg.cmd_plugin)
        self.assertIn("up to date", out)

    def test_validate_fails_on_missing_or_stale_manifests(self):
        self.assertEqual(aicfg.check_plugin(), [])  # no .claude-plugin/: this repo doesn't publish one
        quiet(aicfg.cmd_plugin)
        (self.repo / ".claude-plugin/marketplace.json").unlink()
        errors = aicfg.check_plugin()
        self.assertTrue(any("marketplace.json" in e and "missing" in e and "aicfg.py plugin" in e for e in errors), errors)
        quiet(aicfg.cmd_plugin)
        set_core_version(self.repo, "9.9.9")
        errors = aicfg.check_plugin()
        self.assertTrue(any("plugin.json" in e and "stale" in e for e in errors), errors)
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("aicfg.py plugin", out)


class AicfgHomeTest(TempRepoCase):
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
        os.environ.pop("AICFG_HOME")
        self.assertEqual(aicfg.aicfg_home(), self.home / ".config/ai-config")

    def test_apply_renders_into_aicfg_home(self):
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.aicfg_home / "instructions.md").is_file())
        self.assertTrue((self.aicfg_home / "extensions.md").is_file())
        self.assertTrue(aicfg.extensions_file().is_file())  # deprecated in-repo copy, kept for packs
        self.assertEqual(aicfg.link_target(self.home / ".claude/CLAUDE.md"), self.aicfg_home / "instructions.md")
        self.assertFalse((self.repo / "dist/instructions.md").exists())

    def test_old_dist_link_is_updated_and_old_file_removed(self):
        old = self.repo / "dist/instructions.md"
        old.parent.mkdir()
        old.write_text("old render\n")
        link = self.home / ".claude/CLAUDE.md"
        link.parent.mkdir(parents=True)
        link.symlink_to(old)
        code, out = quiet(aicfg.cmd_sync, False)
        self.assertRegex(out, r"UPDATE +claude +~/.claude/CLAUDE.md")
        quiet(aicfg.cmd_sync, True)
        self.assertEqual(aicfg.link_target(link), self.aicfg_home / "instructions.md")
        self.assertFalse(old.parent.exists())  # the emptied dist/ goes too

    def test_disabled_harness_link_to_aicfg_home_is_pruned(self):
        quiet(aicfg.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[claude]\nenabled = false\n")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".claude/CLAUDE.md").is_symlink())

    def test_doctor_names_the_home_render(self):
        quiet(aicfg.cmd_sync, True)
        (self.repo / "rules/99-new.md").write_text("# New\n\n- Rule.\n")
        fails = [f for f in aicfg.doctor_findings() if f[0] == "FAIL"]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn(aicfg.tilde(self.aicfg_home / "instructions.md"), fails[0][1])


class UserInvokedSkillTest(unittest.TestCase):
    """Codex skips commands that use $ARGUMENTS, so core ships them as user-invoked skills."""

    def test_core_has_no_commands_folder(self):
        self.assertFalse((REPO / "commands").exists())

    def test_skills_taking_arguments_are_user_invoked(self):
        for skill in sorted((REPO / "skills").glob("*/SKILL.md")):
            if "$ARGUMENTS" not in skill.read_text():
                continue
            with self.subTest(skill=skill.parent.name):
                meta = aicfg.frontmatter(skill)
                self.assertEqual(meta.get("disable-model-invocation"), "true")
                self.assertTrue(meta.get("argument-hint"))


class PythonVersionTest(unittest.TestCase):
    def test_old_python_gets_a_message_not_a_traceback(self):
        # Hiding tomllib is what Python 3.10 looks like to the script.
        code = ("import runpy, sys; sys.modules['tomllib'] = None; sys.argv = ['aicfg.py', 'status']; "
                f"runpy.run_path({str(REPO / 'scripts/aicfg.py')!r}, run_name='__main__')")
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
                self.assertEqual(aicfg.satisfies(version, aicfg.parse_constraint(text)), expected)

    def test_rejects_malformed(self):
        for text in ("latest", ">>1", "", ">=0.1,", "=>0.1", "1.2.3.4", ">=1.x", "^1.2", "~=1.2"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                aicfg.parse_constraint(text)


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
        self.core = aicfg.Source("core", self.repo)
        self.srcs = [self.core, aicfg.load_pack(self.acme), aicfg.load_pack(beta)]

    def tearDown(self):
        shutil.rmtree(self.tmp)
        super().tearDown()

    def last_core_rule(self, out: str) -> int:
        last = aicfg.rule_text(aicfg.markdown_files("rules", self.core)[-1])
        return out.index(last) + len(last)

    def test_core_only_render_is_unchanged(self):
        texts = [aicfg.rule_text(p) for p in sorted((self.repo / "rules").glob("*.md"))]
        expected = ("<!-- GENERATED by ai-config from rules/*.md (core). Edit the source repo, "
                    "not this file. -->\n\n" + "\n\n".join(texts) + "\n")
        self.assertEqual(aicfg.render_instructions([self.core]), expected)

    def test_pack_rules_follow_every_core_rule(self):
        out = aicfg.render_instructions(self.srcs)
        self.assertLess(self.last_core_rule(out), out.index("- Early acme rule."))

    def test_pack_blocks_are_labelled_in_source_order(self):
        out = aicfg.render_instructions(self.srcs)
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
        out = aicfg.render_instructions(self.srcs)
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
        self.assertEqual(aicfg.rule_text(rule), "# X\n\n- X rule.")
        plain = self.repo / "rules/51-y.md"
        plain.write_text("# Y\n\n- Y rule.\n")
        self.assertEqual(aicfg.rule_text(plain), "# Y\n\n- Y rule.")

    def test_render_and_budget_leave_out_the_trigger(self):
        out = aicfg.render_instructions()
        self.assertIn("# Working agreements", out)
        self.assertNotIn("trigger:", out)
        _, items = aicfg.always_tokens(aicfg.Source("core", self.repo))
        rule = self.repo / "rules/00-core.md"
        self.assertIn((aicfg.estimate_tokens(aicfg.rule_text(rule)), "rules/00-core.md"), items)

    def test_core_rules_need_a_trigger(self):
        (self.repo / "rules/50-x.md").write_text("# X\n\n- X rule.\n")
        code, out = quiet(aicfg.cmd_validate)
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
        self.renders = self.aicfg_home / "opencode/agents"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def write_agent(self, name: str, meta: str) -> Path:
        path = self.repo / "agents" / f"{name}.md"
        path.write_text(f"---\nname: {name}\ndescription: Fixture agent.\n{meta}---\n\n## Role\nBody.\n")
        return path

    def test_tools_become_denies_and_model_is_dropped(self):
        out = aicfg.opencode_agent(self.write_agent("fixture", "tools: Read, Grep\nmodel: sonnet\n"))
        self.assertTrue(out.startswith("---\nname: fixture\ndescription: Fixture agent.\nmode: subagent\n"), out)
        self.assertTrue(out.endswith("---\n\n## Role\nBody.\n"), out)
        for key in ("edit", "bash", "glob", "webfetch", "websearch", "task", "todowrite"):
            self.assertIn(f"\n  {key}: deny\n", out)
        for key in ("read", "grep", "list"):
            self.assertNotIn(f"  {key}: deny", out)
        self.assertNotIn("model", out)
        self.assertNotIn("tools", out)

    def test_agent_without_tools_keeps_every_permission(self):
        out = aicfg.opencode_agent(self.write_agent("open", ""))
        self.assertNotIn("permission", out)
        self.assertIn("mode: subagent", out)

    def test_apply_links_rendered_agents(self):
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        link = self.agents / "analyst.md"
        self.assertEqual(aicfg.link_target(link), self.renders / "analyst.md")
        self.assertIn("mode: subagent", link.read_text())
        self.assertEqual(aicfg.link_target(self.home / ".claude/agents/analyst.md"), self.repo / "agents/analyst.md")
        self.assertEqual(aicfg.doctor_findings(), [])

    def test_removed_agent_is_pruned(self):
        quiet(aicfg.cmd_sync, True)
        (self.repo / "agents/verifier.md").unlink()
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.agents / "verifier.md").is_symlink())
        self.assertFalse((self.renders / "verifier.md").exists())

    def test_doctor_flags_a_stale_render(self):
        quiet(aicfg.cmd_sync, True)
        (self.renders / "analyst.md").write_text("old\n")
        fails = [f for f in aicfg.doctor_findings() if f[0] == "FAIL"]
        self.assertEqual(len(fails), 1, fails)
        self.assertIn("opencode/agents/analyst.md is stale", fails[0][1])

    def test_unknown_agents_format_is_an_error(self):
        (self.repo / "harnesses.local.toml").write_text('[opencode]\nagents_format = "nope"\n')
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("agents_format", out)


class CrashRegressionTest(TempRepoCase):
    """Problems the Rust parity work found aicfg crashing on instead of reporting."""

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
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("skills/terraform/gone.md: dangling symlink", out)
        code, out = quiet(aicfg.cmd_tokens)
        self.assertEqual(code, 0, out)

    def break_fragment(self):
        fragment = self.repo / "overrides/claude/settings.fragment.json"
        fragment.write_text('{"hooks": {,}}\n')
        return "overrides/claude/settings.fragment.json: invalid JSON"

    def test_invalid_fragment_stops_apply_before_writing(self):
        error = self.break_fragment()
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn(f"ERROR {error}", out)
        self.assertIn("Nothing written", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_invalid_fragment_is_a_doctor_finding(self):
        quiet(aicfg.cmd_sync, True)
        error = self.break_fragment()
        fails = [f[1] for f in aicfg.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any(error in f for f in fails), fails)

    def test_invalid_fragment_in_plugin_and_validate(self):
        (self.repo / ".claude-plugin").mkdir()
        error = self.break_fragment()
        code, out = quiet(aicfg.cmd_plugin)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR", out)
        self.assertIn("invalid JSON", out)
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertEqual(out.count(error), 1, out)

    def test_unknown_agents_format_is_a_doctor_finding(self):
        (self.repo / "harnesses.local.toml").write_text('[opencode]\nagents_format = "nope"\n')
        fails = [f for f in aicfg.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any("agents_format" in what and "opencode" in fix for _, what, fix in fails), fails)

    def test_new_hook_events_keep_fragment_order(self):
        events = ["Stop", "SessionStart", "PostToolUse", "Notification", "UserPromptSubmit",
                  "PreCompact", "SubagentStop", "SessionEnd"]
        group = {"hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/ai-config/x.py"}]}
        fragment = {"hooks": {e: [group] for e in events}}
        merged = aicfg.merge_settings({"hooks": {"PreToolUse": [FOREIGN]}}, fragment)
        self.assertEqual(list(merged["hooks"]), ["PreToolUse", *events])


class InstalledModeTest(TempRepoCase):
    """aicfg installed with pipx/uv: core comes bundled as aicfg/_core and is never written to."""

    def setUp(self):
        super().setUp()
        self.pkg = Path(tempfile.mkdtemp()) / "aicfg"
        self.core = self.pkg / "_core"
        copy_repo(self.core)
        roles = self.core / "skills/spec-agent/roles"
        roles.unlink()
        shutil.copytree(self.core / "agents", roles)  # wheels copy the link's files
        aicfg.config.REPO = self.core
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
        self.assertEqual(aicfg.config.find_core(self.pkg), self.core)
        self.assertEqual(aicfg.config.find_core(self.repo / "aicfg"), self.repo)
        self.assertTrue(aicfg.config.installed())

    def test_local_files_live_in_aicfg_home(self):
        self.aicfg_home.mkdir(parents=True)
        (self.aicfg_home / "harnesses.local.toml").write_text("[cursor]\nenabled = false\n")
        (self.core / "harnesses.local.toml").write_text("[codex]\nenabled = false\n")
        harnesses = aicfg.config.load_harnesses()
        self.assertNotIn("cursor", harnesses)
        self.assertIn("codex", harnesses)
        (self.aicfg_home / "rules").mkdir()
        (self.aicfg_home / "rules/99-mine.local.md").write_text("- My local rule.\n")
        self.assertIn("- My local rule.", aicfg.render_instructions())

    def test_apply_never_writes_inside_the_package(self):
        (self.core / "skills/spec-agent/references/extensions.md").unlink(missing_ok=True)
        before = self.files()
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.files(), before)
        self.assertTrue((self.aicfg_home / "extensions.md").is_file())
        self.assertEqual(aicfg.link_target(self.home / ".claude/skills/spec-agent"), self.core / "skills/spec-agent")
        self.assertEqual(aicfg.doctor_findings(), [])

    def test_relative_pack_path_is_relative_to_aicfg_home(self):
        self.aicfg_home.mkdir(parents=True)
        shutil.copytree(REPO / "examples/pack-acme", self.aicfg_home / "packs/acme")
        (self.aicfg_home / "packs.local.toml").write_text('[acme]\npath = "packs/acme"\n')
        self.assertEqual([s.root for s in aicfg.sources()][-1], self.aicfg_home / "packs/acme")

    def test_hints_name_the_installed_command(self):
        fixes = [fix for _, _, fix in aicfg.doctor_findings()]  # nothing applied yet
        self.assertIn("aicfg apply", fixes)
        self.assertFalse(any("scripts/aicfg.py" in f for f in fixes), fixes)
        code, out = quiet(aicfg.main, ["aicfg", "bogus"])
        self.assertEqual(code, 2)
        self.assertIn("  aicfg status", out)
        self.assertNotIn("aicfg.py", out)

    def test_plugin_needs_a_checkout(self):
        code, out = quiet(aicfg.cmd_plugin)
        self.assertEqual(code, 1, out)
        self.assertIn("checkout", out)

    def test_copied_roles_are_fine_when_installed(self):
        self.assertIsNone(aicfg.check_roles_link())

    def test_tokens_match_a_checkout(self):
        _, installed = quiet(aicfg.cmd_tokens)
        aicfg.config.REPO = self.repo
        _, checkout = quiet(aicfg.cmd_tokens)
        self.assertEqual(installed, checkout)


def git(*args, cwd=None):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                   cwd=cwd, check=True, capture_output=True)


class GitPackTest(TempRepoCase):
    """A pack named by git URL: aicfg fetches it into $AICFG_HOME/packs/<key> (#50)."""

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
        self.clone = self.aicfg_home / "packs/acme"

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
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn(f"FETCH     acme      {self.url} (v1)", out)
        self.assertTrue((self.clone / "pack.toml").is_file())
        self.assertTrue((self.home / ".claude/skills/acme-context").is_symlink())
        self.assertFalse((self.home / ".claude/skills/acme-new").exists())
        self.assertEqual(aicfg.doctor_findings(), [])

    def test_status_does_not_fetch(self):
        self.use(git=self.url)
        code, out = quiet(aicfg.cmd_sync, False)
        self.assertEqual(code, 0, out)
        self.assertIn("FETCH", out)
        self.assertFalse(self.clone.exists())

    def test_update_moves_to_a_new_ref(self):
        self.use(git=self.url, ref="v1")
        quiet(aicfg.cmd_sync, True)
        self.use(git=self.url, ref="v2")
        code, out = quiet(aicfg.cmd_update)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.home / ".claude/skills/acme-new").is_symlink())

    def test_failed_fetch_writes_nothing(self):
        self.use(git=(self.tmp / "missing.git").as_uri())
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR", out)
        self.assertIn("Nothing written", out)
        self.assertFalse(self.clone.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_update_leaves_a_changed_clone_alone(self):
        self.use(git=self.url, ref="v1")
        quiet(aicfg.cmd_sync, True)
        (self.clone / "pack.toml").write_text((self.clone / "pack.toml").read_text() + "# mine\n")
        code, out = quiet(aicfg.cmd_update)
        self.assertEqual(code, 1, out)
        self.assertIn("local changes", out)
        self.assertTrue((self.clone / "pack.toml").read_text().endswith("# mine\n"))

    def test_path_and_git_together_is_an_error(self):
        self.use(git=self.url, path="somewhere")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("`path` or `git`", out)

    def test_url_that_looks_like_an_option_is_refused(self):
        self.use(git="--upload-pack=touch x")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR", out)

    def test_doctor_flags_an_unfetched_pack(self):
        self.use(git=self.url)
        fails = [f for f in aicfg.doctor_findings() if f[0] == "FAIL"]
        self.assertTrue(any("not fetched" in what for _, what, _ in fails), fails)


class HarnessPluginTest(TempRepoCase):
    """A harness `plugin` key links overrides/<harness>/plugin.js (OpenCode's guard plugin)."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        self.link = self.home / ".config/opencode/plugins/ai-config-guard.js"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        super().tearDown()

    def test_apply_links_the_plugin_and_doctor_is_clean(self):
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(aicfg.link_target(self.link), self.repo / "overrides/opencode/plugin.js")
        self.assertEqual(aicfg.doctor_findings(), [])

    def test_disabling_the_harness_prunes_the_plugin(self):
        quiet(aicfg.cmd_sync, True)
        (self.repo / "harnesses.local.toml").write_text("[opencode]\nenabled = false\n")
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse(self.link.is_symlink())

    def test_validate_needs_the_plugin_file(self):
        (self.repo / "overrides/opencode/plugin.js").unlink()
        code, out = quiet(aicfg.cmd_validate)
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
        m = aicfg.SettingsMerge("cursor", self.hooks_json, [(CURSOR_FRAGMENT, "~/.cursor/hooks/ai-config")])
        return m.wanted(), m.markers()

    def test_merge_keeps_foreign_entries_replaces_ours_and_is_idempotent(self):
        wanted, markers = self.wanted()
        old = {"command": "python3 ~/.cursor/hooks/ai-config/old.py"}
        current = {"version": 1, "hooks": {"beforeShellExecution": [CURSOR_FOREIGN, old]}}
        once = aicfg.merge_settings(current, wanted, markers)
        shell = once["hooks"]["beforeShellExecution"]
        self.assertEqual(shell[0], CURSOR_FOREIGN)
        self.assertNotIn(old, shell)
        self.assertIn('python3 "$HOME/.cursor/hooks/ai-config/guard.py"', [e["command"] for e in shell])
        self.assertIn("beforeReadFile", once["hooks"])
        self.assertEqual(aicfg.merge_settings(once, wanted, markers), once)

    def test_a_new_file_gets_version_1_and_a_users_version_is_kept(self):
        wanted, markers = self.wanted()
        self.assertEqual(aicfg.merge_settings({}, wanted, markers)["version"], 1)
        self.assertEqual(aicfg.merge_settings({"version": 2}, wanted, markers)["version"], 2)

    def test_claude_fragment_adds_no_top_level_keys(self):
        m = aicfg.SettingsMerge("claude", self.home / "s.json", [(FRAGMENT, "~/.claude/hooks/ai-config")])
        self.assertEqual(set(aicfg.merge_settings({}, m.wanted(), m.markers())), {"hooks"})

    def test_apply_writes_hooks_json_links_the_hooks_dir_and_doctor_is_clean(self):
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(code, 0, out)
        data = json.loads(self.hooks_json.read_text())
        self.assertEqual(data["version"], 1)
        self.assertEqual(aicfg.link_target(self.home / ".cursor/hooks/ai-config"),
                         self.repo / "overrides/cursor/hooks")
        self.assertEqual(aicfg.doctor_findings(), [])
        code, out = quiet(aicfg.cmd_sync, True)
        self.assertEqual(json.loads(self.hooks_json.read_text()), data)


class CursorPluginTest(TempRepoCase):
    """.cursor-plugin/plugin.json: Cursor's manifest, generated like the others."""

    def manifest(self):
        return json.loads(aicfg.plugin_manifests()[".cursor-plugin/plugin.json"])

    def test_manifest_points_at_core_and_runs_the_cursor_guard(self):
        set_core_version(self.repo, "1.2.3")
        plugin = self.manifest()
        self.assertEqual((plugin["name"], plugin["version"], plugin["license"]), ("ai-config", "1.2.3", "MIT"))
        self.assertEqual((plugin["skills"], plugin["agents"], plugin["rules"]), ("./skills/", "./agents/", "./rules/"))
        self.assertEqual(plugin["hooks"]["version"], 1)
        commands = [e["command"] for entries in plugin["hooks"]["hooks"].values() for e in entries]
        self.assertEqual(set(plugin["hooks"]["hooks"]), {"beforeShellExecution", "beforeReadFile"})
        self.assertTrue(all(c == 'python3 "${CURSOR_PLUGIN_ROOT}/overrides/cursor/hooks/guard.py"'
                            for c in commands), commands)
        self.assertNotIn("..", json.dumps(plugin))

    def test_validate_reports_a_missing_cursor_manifest(self):
        quiet(aicfg.cmd_plugin)
        self.assertEqual(aicfg.check_plugin(), [])
        (self.repo / ".cursor-plugin/plugin.json").unlink()
        self.assertTrue(any(".cursor-plugin/plugin.json" in e and "missing" in e for e in aicfg.check_plugin()))

    def test_rules_need_always_apply(self):
        rule = self.repo / "rules/10-git.md"
        rule.write_text(rule.read_text().replace("alwaysApply: true\n", ""))
        code, out = quiet(aicfg.cmd_validate)
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
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertIn("(packs: acme)", out)

    def test_catches_pack_errors(self):
        (self.pack / "pack.toml").write_text(PACK_TOML.replace('skills = ["acme-deploy"]', 'skills = ["nope"]')
                                             .replace('connector = "ticket-github"', 'connector = "ticket-ghost"'))
        (self.pack / "skills/unprefixed").mkdir()
        (self.pack / "skills/unprefixed/SKILL.md").write_text("---\nname: unprefixed\ndescription: x\n---\n")
        (self.pack / "tripwires.toml").write_text(
            '[[tripwire]]\nid = "T1"\npattern = "Acme rule"\nallow = "(?i)never"\nmessage = "stale rule"\n')
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        for expected in ("acme:skills/unprefixed: pack skills must start with `acme-`",
                         "domains names unknown skill `nope`",
                         "ticket.connector names unknown skill `ticket-ghost`",
                         "acme:rules/50-acme.md:3: tripwire T1: stale rule"):
            self.assertIn(expected, out)

    def test_compatible_pack_has_no_version_message(self):
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertNotIn("requires_core", out)

    def test_incompatible_pack_fails(self):
        set_requires_core(self.pack, 'requires_core = ">=1.3"')
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:pack.toml: requires_core `>=1.3` is not satisfied by core 1.2.3", out)

    def test_incompatible_enabled_pack_fails_plain_validate(self):
        set_requires_core(self.pack, 'requires_core = "<1"')
        (self.repo / "packs.local.toml").write_text(f'[acme]\npath = "{self.pack}"\n')
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("requires_core `<1` is not satisfied by core 1.2.3", out)

    def test_missing_requires_core_warns(self):
        set_requires_core(self.pack, "")
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN acme:pack.toml: no `requires_core`", out)
        set_core_version(self.repo, "0.3.1")
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertIn('requires_core = ">=0.3, <0.4"', out)  # 0.x: breaking changes bump MINOR

    def test_malformed_requires_core_fails(self):
        set_requires_core(self.pack, 'requires_core = "latest"')
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:pack.toml: invalid requires_core `latest`", out)
        self.assertIn('">=0.1, <0.2"', out)  # shows the accepted syntax

    def test_invalid_core_version_fails(self):
        (self.repo / "VERSION").write_text("one\n")
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 1)
        self.assertIn("VERSION: `one` is not MAJOR.MINOR.PATCH", out)

    def test_tripwire_allow_pattern_passes_line(self):
        (self.pack / "rules/50-acme.md").write_text("- Never use the old Acme rule.\n")
        (self.pack / "tripwires.toml").write_text(
            '[[tripwire]]\nid = "T1"\npattern = "Acme rule"\nallow = "(?i)never"\n')
        code, out = quiet(aicfg.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)


class ChangelogCheckTest(TempRepoCase):
    """validate keeps VERSION and the newest CHANGELOG entry in step, with no Unreleased section."""

    def setUp(self):
        super().setUp()
        set_core_version(self.repo, "1.2.3")

    def test_matching_changelog_passes(self):
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_version_without_changelog_entry_fails(self):
        (self.repo / "VERSION").write_text("1.2.4\n")
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md: newest version 1.2.3 doesn't match VERSION 1.2.4", out)

    def test_unreleased_section_fails(self):
        (self.repo / "CHANGELOG.md").write_text(
            "# Changelog\n\n## Unreleased\n\n- New.\n\n## 1.2.3 (2026-01-01)\n\n- Change.\n")
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("CHANGELOG.md: has an `## Unreleased` section", out)

    def test_changelog_without_version_heading_fails(self):
        (self.repo / "CHANGELOG.md").write_text("# Changelog\n")
        code, out = quiet(aicfg.cmd_validate)
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
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_core_connector_missing_an_operation_fails(self):
        write_skill(self.repo, "ticket-x", "## fetch\n\n## comment\n\n## transition\n")
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("skills/ticket-x/SKILL.md: connector missing `##` sections for link_pr", out)

    def test_one_heading_may_name_several_operations(self):
        write_skill(self.repo, "ticket-y", "## fetch (read-only)\n\n## comment / transition / link_pr\n")
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_pack_connector_missing_operations_fails(self):
        pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack",
                         PACK_TOML.replace('connector = "ticket-github"', 'connector = "acme-tickets"'))
        self.addCleanup(shutil.rmtree, pack.parent)
        write_skill(pack, "acme-tickets", "## fetch\n")
        code, out = quiet(aicfg.cmd_validate, str(pack))
        self.assertEqual(code, 1)
        self.assertIn("acme:skills/acme-tickets/SKILL.md: connector missing `##` sections for "
                      "comment, transition, link_pr", out)


class ExamplePackTest(unittest.TestCase):
    """examples/pack-acme is the copyable template: it must pass against the real core VERSION."""

    def test_example_pack_is_valid_without_warnings(self):
        code, out = quiet(aicfg.cmd_validate, str(REPO / "examples/pack-acme"))
        self.assertEqual(code, 0, out)
        self.assertNotIn("WARN", out)
        self.assertIn("(packs: acme)", out)


class ValidateTest(unittest.TestCase):
    def test_repo_is_valid(self):
        code, out = quiet(aicfg.cmd_validate)
        self.assertEqual(code, 0, out)

    def test_catches_placeholder_without_hooks_dir(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            copy_repo(tmp)
            toml = tmp / "harnesses.toml"
            toml.write_text(toml.read_text().replace('hooks_dir = "~/.claude/hooks/ai-config"\n', ""))
            old = aicfg.config.REPO
            aicfg.config.REPO = tmp
            try:
                code, out = quiet(aicfg.cmd_validate)
            finally:
                aicfg.config.REPO = old
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
            old = aicfg.config.REPO
            aicfg.config.REPO = tmp
            try:
                code, out = quiet(aicfg.cmd_validate)
            finally:
                aicfg.config.REPO = old
            self.assertEqual(code, 1)
            for expected in ("unknown agent `ghost`", "broken link `missing.md`",
                             "unknown skill `nope`", "unknown model `gpt-9`"):
                self.assertIn(expected, out)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
