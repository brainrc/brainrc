"""Tests for scripts/aicfg.py: settings merge, sync against a fake HOME, and validation."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("aicfg", REPO / "scripts" / "aicfg.py")
aicfg = importlib.util.module_from_spec(spec)
sys.modules["aicfg"] = aicfg  # dataclasses look the module up while decorating
spec.loader.exec_module(aicfg)

FOREIGN = {"hooks": [{"type": "command", "command": "node /opt/other/hook.js"}]}
OURS_OLD = {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/ai-config/old.py"}]}
SOURCES = ("skills", "agents", "commands", "overrides", "rules")
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


class TempRepoCase(unittest.TestCase):
    """Point aicfg at a throwaway copy of the repo, so tests never read local config or write dist/."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        copy_repo(self.repo)
        self.old_repo = aicfg.REPO
        aicfg.REPO = self.repo

    def tearDown(self):
        aicfg.REPO = self.old_repo
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
        (self.repo / "VERSION").write_text("1.2.3\n")
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

        rules = (self.repo / "dist/instructions.md").read_text()
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
        self.assertNotIn("- Acme rule.", (self.repo / "dist/instructions.md").read_text())
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


class PackValidateTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        (self.repo / "VERSION").write_text("1.2.3\n")

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
        (self.repo / "VERSION").write_text("0.3.1\n")
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
            old = aicfg.REPO
            aicfg.REPO = tmp
            try:
                code, out = quiet(aicfg.cmd_validate)
            finally:
                aicfg.REPO = old
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
            old = aicfg.REPO
            aicfg.REPO = tmp
            try:
                code, out = quiet(aicfg.cmd_validate)
            finally:
                aicfg.REPO = old
            self.assertEqual(code, 1)
            for expected in ("unknown agent `ghost`", "broken link `missing.md`",
                             "unknown skill `nope`", "unknown model `gpt-9`"):
                self.assertIn(expected, out)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
