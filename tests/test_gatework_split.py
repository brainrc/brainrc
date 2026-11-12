"""The syncer split from spec-agent (#172): Gatework as a bundled pack with its own validator plugin."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import PACK_TOML, TempRepoCase, brainrc, install_harnesses, make_pack, quiet, set_core_version  # noqa: E402

LEGACY_TOML = PACK_TOML.replace("[extensions.gatework]", "[extensions]").replace("extensions.gatework.", "extensions.")


class SplitCase(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp())
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        install_harnesses(self.home)
        set_core_version(self.repo, "1.2.3")
        self.pack = Path(tempfile.mkdtemp()).resolve() / "acme-pack"

    def tearDown(self):
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        shutil.rmtree(self.pack.parent)
        super().tearDown()

    def packs(self, text: str) -> None:
        (self.repo / "packs.local.toml").write_text(text)

    def acme(self, pack_toml: str = PACK_TOML, extra: str = "") -> None:
        make_pack(self.pack, pack_toml)
        self.packs(f'[acme]\npath = "{self.pack}"\n{extra}')


class ZeroPacksTest(SplitCase):
    """Done when: brainrc with zero packs installs nothing and passes validate."""

    def setUp(self):
        super().setUp()
        self.packs("[gatework]\nenabled = false\n")

    def test_validate_passes(self):
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertIn("OK: 0 skills, 0 agents, 0 commands", out)

    def test_apply_installs_no_skills_or_agents_and_no_extensions_file(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        for d in (".claude/skills", ".claude/agents", ".codex/skills", ".cursor/skills"):
            found = list((self.home / d).iterdir()) if (self.home / d).is_dir() else []
            self.assertEqual(found, [], d)
        self.assertTrue((self.settings_home / "instructions.md").is_file())  # core's rules still install
        self.assertFalse((self.settings_home / "extensions.md").exists())
        self.assertEqual(brainrc.doctor_findings(), [])

    def test_disabling_gatework_later_prunes_it(self):
        (self.repo / "packs.local.toml").unlink()
        quiet(brainrc.cmd_sync, True)
        self.assertTrue((self.home / ".claude/skills/spec-agent").is_symlink())
        self.assertTrue((self.settings_home / "extensions.md").is_file())
        self.packs("[gatework]\nenabled = false\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse(os.path.lexists(self.home / ".claude/skills/spec-agent"))
        self.assertFalse((self.settings_home / "extensions.md").exists())


class ExtensionsTest(SplitCase):
    def test_namespaced_extensions_render_without_warnings(self):
        self.acme()
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertNotIn("WARN", out)
        quiet(brainrc.cmd_sync, True)
        self.assertIn("- (acme) Deploy plan reviewed", (self.settings_home / "extensions.md").read_text())

    def test_legacy_top_level_extensions_still_render_with_a_warning(self):
        self.acme(LEGACY_TOML)
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertIn("[extensions] `domains` is deprecated; move it under [extensions.gatework]", out)
        quiet(brainrc.cmd_sync, True)
        ext = (self.settings_home / "extensions.md").read_text()
        self.assertIn("| `deploy/*.yaml` | acme-deploy | brainrc-infra-reviewer | acme |", ext)

    def test_spec_agent_table_passes_through_with_a_warning(self):
        self.acme(PACK_TOML.replace("extensions.gatework", "extensions.spec-agent"))
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertIn("[extensions.spec-agent] is deprecated", out)
        quiet(brainrc.cmd_sync, True)
        self.assertIn('"connector": "ticket-github"', (self.settings_home / "extensions.md").read_text())

    def test_errors_in_the_gatework_table_come_from_its_plugin(self):
        self.acme(PACK_TOML.replace('skills = ["acme-deploy"]', 'skills = ["acme-nope"]'))
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("acme:pack.toml: domains names unknown skill `acme-nope`", out)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("Nothing written", out)

    def test_a_table_no_enabled_pack_reads_is_a_warning(self):
        self.acme(PACK_TOML + "\n[extensions.other]\nx = 1\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertIn("no enabled pack reads [extensions] `other`", out)

    def test_gatework_extensions_with_gatework_disabled_warn_and_apply(self):
        self.acme(extra="\n[gatework]\nenabled = false\n")
        (self.pack / "pack.toml").write_text(PACK_TOML.replace('reviewer = "brainrc-infra-reviewer"\n', ""))
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertIn("no enabled pack reads [extensions] `gatework`", out)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)


class PluginTrustTest(SplitCase):
    PLUGIN = 'def check(me, srcs):\n    return [f"{me.name}: plugin ran"]\n'

    def acme_with_plugin(self, extra: str = "", body: str = PLUGIN) -> None:
        self.acme(PACK_TOML.replace('prefix = "acme-"\n', 'prefix = "acme-"\nvalidator = "check.py"\n'), extra)
        (self.pack / "check.py").write_text(body)

    def test_a_configured_packs_validator_runs_only_when_trusted(self):
        self.acme_with_plugin()
        code, out = quiet(brainrc.cmd_validate)
        self.assertNotIn("plugin ran", out)
        self.assertIn("ships a validator that brainrc doesn't run; set `run_validator = true` for [acme]", out)
        self.packs(f'[acme]\npath = "{self.pack}"\nrun_validator = true\n')
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR acme: plugin ran", out)

    def test_doctor_runs_no_untrusted_validator(self):
        self.acme_with_plugin(body="raise SystemExit('ran')\n")
        findings = brainrc.doctor_findings()
        self.assertFalse(any("ran" in f[1] or "validator" in f[1] for f in findings), findings)

    def test_only_core_bundles_a_pack(self):
        make_pack(self.repo / "packs/acme")
        self.packs("[acme]\nbundled = true\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("`bundled` is only for the packs core ships", out)
        self.packs('[acme]\npath = "packs/acme"\n')
        self.assertFalse(brainrc.load_pack(self.repo / "packs/acme", "acme").bundled)

    def test_validate_pack_runs_the_packs_own_validator(self):
        self.acme_with_plugin()
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1, out)
        self.assertIn("acme: plugin ran", out)

    def test_a_broken_validator_stops_apply(self):
        self.acme_with_plugin("run_validator = true\n", "raise RuntimeError('boom')\n")
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 1, out)
        self.assertIn("acme:check.py: validator failed to load (RuntimeError: boom)", out)

    def test_a_validator_that_raises_is_an_error_not_a_crash(self):
        self.acme_with_plugin("run_validator = true\n", "def check(me, srcs):\n    raise KeyError('x')\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("acme:check.py: check failed (KeyError: 'x')", out)

    def test_validator_outside_the_pack_is_refused(self):
        self.acme(PACK_TOML.replace('prefix = "acme-"\n', 'prefix = "acme-"\nvalidator = "../x.py"\n'))
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1, out)
        self.assertIn("`validator` must name a .py file in the pack", out)


class GateworkPackTest(unittest.TestCase):
    ROOT = Path(__file__).resolve().parent.parent

    def test_the_pack_is_self_contained(self):
        pack = self.ROOT / "packs/gatework"
        for p in pack.rglob("*"):
            if p.is_symlink():
                with self.subTest(link=str(p.relative_to(pack))):
                    self.assertTrue(p.resolve().is_relative_to(pack), "a link that leaves the pack breaks the move")
        meta = brainrc.load_pack(pack, "gatework").meta
        self.assertEqual((meta["id"], meta["validator"]), ("brainrc/gatework", "validator.py"))

    def test_spec_agent_is_a_deprecated_alias_for_one_minor_release(self):
        skills = self.ROOT / "packs/gatework/skills"
        alias = brainrc.frontmatter(skills / "spec-agent/SKILL.md")
        self.assertEqual(brainrc.frontmatter(skills / "brainrc-gatework/SKILL.md")["name"], "brainrc-gatework")
        self.assertEqual(alias["description"], "Deprecated, use brainrc-gatework (removed in 0.8.0)")
        self.assertEqual(alias["disable-model-invocation"], "true")
        self.assertIn("`brainrc-gatework` skill", (skills / "spec-agent/SKILL.md").read_text())
        for name in ("brainrc-work", "brainrc-plan", "spec-approve", "spec-resume"):
            with self.subTest(skill=name):
                text = (skills / name / "SKILL.md").read_text()
                self.assertIn("`brainrc-gatework` skill", text)
                self.assertNotIn("`spec-agent` skill", text)

    def test_core_holds_no_spec_agent_knowledge(self):
        for name in ("EXTENSION_KEYS", "ROLES_LINK", "REQUIRED_CONNECTOR_OPS", "extensions_file"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(brainrc.config, name))
        for name in ("check_connectors", "check_roles_link"):
            self.assertFalse(hasattr(brainrc.validate, name))


if __name__ == "__main__":
    unittest.main()
