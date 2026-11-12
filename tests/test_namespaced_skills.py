"""Namespaced core skills (specs/149-1-namespaced-skills); the old aliases were removed in 0.6.1."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet, set_core_version  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NAMES = ("work", "review", "plan", "aws", "terraform")
USER_INVOKED = ("work", "review", "plan")  # slash commands: take $ARGUMENTS
KNOWLEDGE = ("aws", "terraform")           # auto-triggered today
ARGUMENT_HINTS = {
    "work": "<gh:42 | jira:PROJ-7 | issue URL | local:path.md | free text | --campaign <epic|query>> "
            "[--local] [--batch-size N] [--dry-run] [--shape playbook|ordered] [--auto]",
    "review": "[extra focus]",
    "plan": "<topic> [--web] [--dry-run] [--oneshot] [--local]",
}
TRIGGER_STARTS = {  # the original auto-trigger descriptions, which move to the brainrc- twin
    "aws": "AWS account safety, CLI usage, and review checklists",
    "terraform": "Terraform/OpenTofu and Terragrunt conventions",
}


def meta(root, name):
    path = Path(root) / "skills" / name / "SKILL.md"
    return brainrc.frontmatter(path) if path.is_file() else {}


def body(root, name):
    path = Path(root) / "skills" / name / "SKILL.md"
    return path.read_text().split("\n---\n", 1)[-1] if path.is_file() else ""


class NamespacedSkillsTest(unittest.TestCase):
    """AC1: five brainrc-* skills with the old behavior and content."""

    def test_namespaced_skills_exist_with_matching_name(self):
        for n in NAMES:
            with self.subTest(skill=n):
                self.assertTrue((ROOT / f"skills/brainrc-{n}/SKILL.md").is_file(), f"skills/brainrc-{n} missing")
                self.assertEqual(meta(ROOT, f"brainrc-{n}").get("name"), f"brainrc-{n}")

    def test_user_invoked_skills_keep_hint_and_flag(self):
        for n in USER_INVOKED:
            with self.subTest(skill=n):
                m = meta(ROOT, f"brainrc-{n}")
                self.assertEqual(m.get("argument-hint"), ARGUMENT_HINTS[n])
                self.assertEqual(m.get("disable-model-invocation"), "true")
                self.assertIn("$ARGUMENTS", body(ROOT, f"brainrc-{n}"))

    def test_work_body_is_unchanged(self):
        self.assertIn("Use the `spec-agent` skill to work on this item end to end:",
                      body(ROOT, "brainrc-work"))

    def test_knowledge_skills_keep_trigger_description_and_stay_auto_triggerable(self):
        for n in KNOWLEDGE:
            with self.subTest(skill=n):
                m = meta(ROOT, f"brainrc-{n}")
                self.assertTrue(m.get("description", "").startswith(TRIGGER_STARTS[n]), m.get("description"))
                self.assertNotIn("disable-model-invocation", m)
        self.assertIn("## Account safety", body(ROOT, "brainrc-aws"))


class RemovedAliasesTest(unittest.TestCase):
    """The old names were removed in 0.6.1, as announced for 0.6.0."""

    def test_old_names_are_gone(self):
        for n in NAMES:
            with self.subTest(skill=n):
                self.assertFalse((ROOT / "skills" / n).exists(), f"skills/{n} should be removed")

    def test_alias_check_is_gone(self):
        self.assertFalse(hasattr(brainrc.validate, "DEPRECATED_ALIASES"))
        self.assertFalse(hasattr(brainrc.validate, "_check_aliases"))


class PluginManifestTest(TempRepoCase):
    """AC7: the plugin carries the new names and validate catches a stale manifest."""

    def listed(self, root):
        cursor = json.loads((root / ".cursor-plugin/plugin.json").read_text())
        return {p.name for p in (root / cursor["skills"]).iterdir() if (p / "SKILL.md").is_file()}

    def test_committed_manifests_are_current_and_list_only_the_new_names(self):
        brainrc.config.REPO = ROOT
        try:
            self.assertEqual(brainrc.check_plugin(), [])
        finally:
            brainrc.config.REPO = self.repo
        listed = self.listed(ROOT)
        for n in NAMES:
            with self.subTest(skill=n):
                self.assertIn(f"brainrc-{n}", listed)
                self.assertNotIn(n, listed)

    def test_stale_manifest_fails_validate(self):
        quiet(brainrc.cmd_plugin)
        self.assertEqual(brainrc.check_plugin(), [])
        set_core_version(self.repo, "9.9.9")  # the manifests carry VERSION
        errors = brainrc.check_plugin()
        self.assertTrue(any("stale" in e for e in errors), errors)
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("brainrc.py plugin", out)


if __name__ == "__main__":
    unittest.main()
