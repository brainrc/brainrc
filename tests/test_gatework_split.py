"""The syncer split from spec-agent (#172): Gatework as a default pack with its own validator plugin."""
import os
import shutil
import sys
import tempfile
import tomllib
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
        self.assertIn('"connector": "brainrc-ticket-github"', (self.settings_home / "extensions.md").read_text())

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

    def test_a_default_packs_validator_is_trusted(self):
        (self.repo / "packs/gatework/validator.py").write_text(self.PLUGIN)
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR gatework: plugin ran", out)

    def test_bundled_is_no_longer_a_pack_key(self):
        self.packs("[gatework]\nbundled = true\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 0, out)
        self.assertIn("unknown key `bundled` in [gatework]", out)

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


class CoreTest(unittest.TestCase):
    def test_core_holds_no_spec_agent_knowledge(self):
        for name in ("EXTENSION_KEYS", "ROLES_LINK", "REQUIRED_CONNECTOR_OPS", "extensions_file"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(brainrc.config, name))
        for name in ("check_connectors", "check_roles_link"):
            self.assertFalse(hasattr(brainrc.validate, name))


class DefaultPackTest(SplitCase):
    """Gatework is a default pack: core's packs.toml fetches it from its own repo (#338)."""
    REAL = Path(__file__).resolve().parent.parent

    def test_core_fetches_gatework_from_its_repo_at_a_release_tag(self):
        cfg = tomllib.loads((self.REAL / "packs.toml").read_text())["gatework"]
        self.assertEqual(cfg["git"], "https://github.com/brainrc/gatework.git")
        self.assertRegex(cfg["ref"], r"^v\d+\.\d+\.\d+$")
        self.assertNotIn("path", cfg)
        self.assertFalse((self.REAL / "packs").exists(), "core ships no pack of its own")

    def test_a_local_path_replaces_the_default_packs_git(self):
        (self.repo / "packs.toml").write_text('[gatework]\ngit = "https://example.com/g.git"\nref = "v1.0.0"\n')
        clone = self.repo / "packs/gatework"
        self.packs(f'[gatework]\npath = "{clone}"\n')
        cfg = brainrc.config._layered("packs")["gatework"]
        self.assertEqual(cfg, {"path": str(clone)})
        self.assertEqual(brainrc.sources()[1].root, clone)
        self.assertTrue(brainrc.sources()[1].default)

    def test_a_local_ref_alone_keeps_the_git_url(self):
        (self.repo / "packs.toml").write_text('[gatework]\ngit = "https://example.com/g.git"\nref = "v1.0.0"\n')
        self.packs('[gatework]\nref = "v1.1.0"\n')
        cfg = brainrc.config._layered("packs")["gatework"]
        self.assertEqual((cfg["git"], cfg["ref"]), ("https://example.com/g.git", "v1.1.0"))

    def test_a_pack_enabled_locally_is_not_a_default_pack(self):
        self.acme()
        acme = [s for s in brainrc.sources() if s.key == "acme"][0]
        self.assertFalse(acme.default)

    def test_validate_pack_checks_against_the_default_pack(self):
        self.acme()  # its extensions name brainrc-infra-reviewer and brainrc-ticket-github
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        self.assertIn("(packs: gatework, acme)", out)

    def test_validate_pack_of_the_default_pack_itself_checks_it_once(self):
        code, out = quiet(brainrc.cmd_validate, str(self.repo / "packs/gatework"))
        self.assertEqual(code, 0, out)
        self.assertIn("(packs: gatework)", out)
        self.assertNotIn("duplicate", out.lower())

    def test_validate_pack_says_when_the_default_pack_is_not_fetched(self):
        (self.repo / "packs.toml").write_text('[gatework]\ngit = "https://example.com/g.git"\nref = "v1.0.0"\n')
        self.acme()
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertIn("default pack `gatework` isn't fetched yet, so this pack is checked without it", out)
        self.assertIn("(packs: acme)", out)


if __name__ == "__main__":
    unittest.main()
