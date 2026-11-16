"""validate covers more (#137): links in a pack's README and docs/**, skills named in prose ("the x
skill"), references inside rules, and a pack's own OpenCode plugin."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, install_harnesses, make_pack, quiet, set_core_version  # noqa: E402
from brainrc import config, permissions  # noqa: E402
from brainrc.sources import load_pack  # noqa: E402
from support import home_env, restore_home, rmtree, saved_home  # noqa: E402

FIXTURE = ROOT / "tests/fixtures/pack-prose-refs"


class ProseReferencesTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = Path(tempfile.mkdtemp()).resolve() / "prose"
        self.addCleanup(rmtree, self.pack.parent)
        shutil.copytree(FIXTURE, self.pack)

    def validate(self):
        return quiet(brainrc.cmd_validate, str(self.pack))

    def test_the_fixture_pack_fails_on_each_reference(self):
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        errors = sorted(line for line in out.splitlines() if line.startswith("ERROR"))
        self.assertEqual(errors, [
            "ERROR prose:README.md: broken link `docs/notes.md`",
            "ERROR prose:docs/guide.md: broken link `runbook.md`",
            "ERROR prose:rules/50-prose.md: unknown skill `prose-rollback`",
            "ERROR prose:skills/prose-deploy/SKILL.md: unknown skill `prose-context` "
            "(named as \"the prose-context skill\")",
        ])

    def test_it_passes_once_the_references_resolve(self):
        for name in ("prose-context", "prose-rollback"):
            d = self.pack / "skills" / name
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {name}. Use for tests.\n---\nBody.\n")
        (self.pack / "docs/notes.md").write_text("# Notes\n")
        (self.pack / "docs/runbook.md").write_text("# Runbook\n")
        code, out = self.validate()
        self.assertEqual(code, 0, out)

    def test_prose_that_only_looks_like_a_name_is_left_alone(self):
        skill = self.pack / "skills/prose-deploy/SKILL.md"
        skill.write_text(skill.read_text().replace("the prose-context skill", "The prose-deploy skill"))
        text = skill.read_text() + "\nThe follow-up skill and the in-depth skill are habits, not skills.\n"
        skill.write_text(text + "```\nthe prose-ghost skill (in a code block)\n```\n")
        _, out = self.validate()
        self.assertNotIn("prose:skills/prose-deploy", out)

    def test_a_core_rule_reference_is_checked(self):
        (self.repo / "rules/90-test.md").write_text(
            "---\ntrigger: always_on\nalwaysApply: true\n---\n# Test\n\nUse the `brainrc-ghost` skill.\n")
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR rules/90-test.md: unknown skill `brainrc-ghost`", out)


class PackPluginTest(TempRepoCase):
    """A pack's overrides/opencode/plugin.js is linked beside core's guard plugin."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        self.pack = make_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        (self.pack / "overrides/opencode").mkdir(parents=True)
        (self.pack / "overrides/opencode/plugin.js").write_text("export const AcmeGuard = async () => ({});\n")
        set_core_version(self.repo, "1.2.3")
        self.enable()
        self.plugins = self.home / ".config/opencode/plugins"

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        rmtree(self.pack.parent)
        super().tearDown()

    def enable(self, enabled: bool = True) -> None:
        (self.repo / "packs.local.toml").write_text(
            f"[acme]\npath = '{self.pack}'\nenabled = {str(enabled).lower()}\n")

    def test_apply_links_it_beside_cores_and_removes_it_with_the_pack(self):
        code, out = quiet(brainrc.cmd_sync, True, None, False, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(brainrc.link_target(self.plugins / "brainrc-guard.js"), self.repo / "overrides/opencode/plugin.js")
        self.assertEqual(brainrc.link_target(self.plugins / "brainrc-guard-acme.js"),
                         self.pack / "overrides/opencode/plugin.js")
        self.enable(False)
        code, out = quiet(brainrc.cmd_sync, True, None, False, True)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.plugins / "brainrc-guard-acme.js").is_symlink())
        self.assertTrue((self.plugins / "brainrc-guard.js").is_symlink())

    def test_it_is_recorded_as_a_permission(self):
        perms = permissions.of_pack(load_pack(self.pack, "acme"), [], hooks=True, mcp=False)
        self.assertIn("opencode plugin overrides/opencode/plugin.js", perms["hooks"])

    def test_validate_accepts_it_and_refuses_one_no_harness_loads(self):
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 0, out)
        (self.pack / "overrides/claude/plugin.js").write_text("// nothing loads this\n")
        code, out = quiet(brainrc.cmd_validate, str(self.pack))
        self.assertEqual(code, 1, out)
        self.assertIn("acme:overrides/claude/plugin.js: no harness in harnesses.toml loads a plugin", out)

    def test_the_plugin_path(self):
        self.assertEqual(config.pack_plugin_path("~/.config/opencode/plugins/brainrc-guard.js", "acme"),
                         "~/.config/opencode/plugins/brainrc-guard-acme.js")
        self.assertEqual(config.pack_plugin_path("~/p.d/guard", "acme"), "~/p.d/guard-acme")


if __name__ == "__main__":
    unittest.main()
