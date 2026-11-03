"""Namespaced core skills and their deprecated aliases (specs/149-1-namespaced-skills, AC1 to AC8)."""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet, set_core_version  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NAMES = ("work", "review", "plan", "aws", "terraform")
USER_INVOKED = ("work", "review", "plan")  # slash commands: take $ARGUMENTS
KNOWLEDGE = ("aws", "terraform")           # auto-triggered today
REMOVED_IN = "0.6.0"
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


class AliasContentTest(unittest.TestCase):
    """AC3, AC4, AC5 on the real tree."""

    def test_every_old_name_is_an_alias_naming_its_replacement_and_removal_release(self):
        for n in NAMES:
            with self.subTest(skill=n):
                text = (ROOT / f"skills/{n}/SKILL.md").read_text()
                self.assertEqual(meta(ROOT, n).get("name"), n)
                self.assertIn(f"brainrc-{n}", body(ROOT, n))
                self.assertIn(REMOVED_IN, body(ROOT, n))
                self.assertIn("deprecated", text.lower())
                self.assertLess(len(text.splitlines()), 20, "an alias is a short stub")

    def test_user_invoked_aliases_forward_the_same_arguments(self):
        for n in USER_INVOKED:
            with self.subTest(skill=n):
                b = body(ROOT, n)
                self.assertIn("$ARGUMENTS", b)
                self.assertRegex(b, rf"(?i)(follow|carry out|use|run).*`brainrc-{n}`")

    def test_user_invoked_aliases_keep_argument_hint_for_completion(self):
        for n in USER_INVOKED:
            with self.subTest(skill=n):
                self.assertEqual(meta(ROOT, n).get("argument-hint"), ARGUMENT_HINTS[n])

    def test_knowledge_aliases_tell_the_model_to_read_the_replacement(self):
        for n in KNOWLEDGE:
            with self.subTest(skill=n):
                self.assertRegex(body(ROOT, n), rf"(?i)read.*`brainrc-{n}`")

    def test_every_alias_is_model_disabled_with_a_deprecation_description(self):
        for n in NAMES:
            with self.subTest(skill=n):
                m = meta(ROOT, n)
                self.assertEqual(m.get("disable-model-invocation"), "true")
                d = m.get("description", "")
                self.assertTrue(d.lower().startswith("deprecated"), d)
                self.assertIn(f"brainrc-{n}", d)
                self.assertLessEqual(len(d), 80, "always-loaded token budget")
                self.assertNotEqual(d, meta(ROOT, f"brainrc-{n}").get("description"))

    def test_each_pair_has_exactly_one_auto_triggerable_member(self):
        for n in NAMES:
            with self.subTest(skill=n):
                triggerable = [s for s in (n, f"brainrc-{n}")
                               if (ROOT / "skills" / s / "SKILL.md").is_file()
                               and meta(ROOT, s).get("disable-model-invocation") != "true"]
                expected = [f"brainrc-{n}"] if n in KNOWLEDGE else []
                self.assertEqual(triggerable, expected)


class PluginManifestTest(TempRepoCase):
    """AC7: the plugin carries both names and validate catches a stale manifest."""

    def test_committed_manifests_are_current_and_point_at_a_skills_dir_with_both_names(self):
        brainrc.config.REPO = ROOT
        try:
            self.assertEqual(brainrc.check_plugin(), [])
        finally:
            brainrc.config.REPO = self.repo
        cursor = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text())
        listed = {p.name for p in (ROOT / cursor["skills"]).iterdir() if (p / "SKILL.md").is_file()}
        for n in NAMES:
            self.assertIn(n, listed)
            self.assertIn(f"brainrc-{n}", listed)

    def test_stale_manifest_after_adding_skills_fails_validate(self):
        quiet(brainrc.cmd_plugin)
        self.assertEqual(brainrc.check_plugin(), [])
        set_core_version(self.repo, "9.9.9")  # the manifests carry VERSION
        errors = brainrc.check_plugin()
        self.assertTrue(any("stale" in e for e in errors), errors)
        code, out = quiet(brainrc.cmd_validate)
        self.assertEqual(code, 1)
        self.assertIn("brainrc.py plugin", out)

    def test_generated_plugin_sees_both_names(self):
        quiet(brainrc.cmd_plugin)
        cursor = json.loads((self.repo / ".cursor-plugin/plugin.json").read_text())
        listed = {p.name for p in (self.repo / cursor["skills"]).iterdir() if (p / "SKILL.md").is_file()}
        for n in NAMES:
            self.assertLessEqual({n, f"brainrc-{n}"}, listed)


class AliasNearMissTest(TempRepoCase):
    """AC5, AC8: validate rejects a broken alias in a temp copy of the tree."""

    def alias(self, n):
        return self.repo / "skills" / n / "SKILL.md"

    def validate(self):
        return quiet(brainrc.cmd_validate)

    def rewrite(self, n, fn):
        path = self.alias(n)
        path.write_text(fn(path.read_text()))

    def test_unmodified_copy_validates(self):
        code, out = self.validate()
        self.assertEqual(code, 0, out)

    def test_alias_missing_disable_model_invocation_fails(self):
        for n in NAMES:
            with self.subTest(skill=n):
                original = self.alias(n).read_text()
                self.rewrite(n, lambda t: re.sub(r"(?m)^disable-model-invocation:.*\n", "", t))
                code, out = self.validate()
                self.assertEqual(code, 1, out)
                self.assertIn(f"skills/{n}", out)
                self.assertIn("disable-model-invocation", out)
                self.alias(n).write_text(original)

    def test_alias_with_the_old_trigger_description_fails(self):
        for n in NAMES:
            with self.subTest(skill=n):
                original = self.alias(n).read_text()
                twin = meta(self.repo, f"brainrc-{n}").get("description", "the old trigger text")
                self.rewrite(n, lambda t: re.sub(r"(?m)^description:.*$", lambda _: f"description: {twin}", t, count=1))
                code, out = self.validate()
                self.assertEqual(code, 1, out)
                self.assertIn(f"skills/{n}", out)
                self.alias(n).write_text(original)

    def test_alias_not_naming_its_replacement_fails(self):
        for n in NAMES:
            with self.subTest(skill=n):
                original = self.alias(n).read_text()
                head, sep, rest = original.partition("\n---\n")
                self.alias(n).write_text(head + sep + rest.replace(f"brainrc-{n}", "something-else"))
                code, out = self.validate()
                self.assertEqual(code, 1, out)
                self.assertIn(f"brainrc-{n}", out)
                self.alias(n).write_text(original)

    def test_alias_not_naming_the_removal_release_fails(self):
        for n in NAMES:
            with self.subTest(skill=n):
                original = self.alias(n).read_text()
                head, sep, rest = original.partition("\n---\n")
                self.alias(n).write_text(head + sep + rest.replace(REMOVED_IN, "soon"))
                code, out = self.validate()
                self.assertEqual(code, 1, out)
                self.assertIn(REMOVED_IN, out)
                self.alias(n).write_text(original)

    def test_alias_whose_target_is_missing_fails(self):
        import shutil
        for n in NAMES:
            with self.subTest(skill=n):
                target = self.repo / "skills" / f"brainrc-{n}"
                backup = self.repo / f"backup-{n}"
                if target.exists():
                    shutil.move(target, backup)
                try:
                    code, out = self.validate()
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"brainrc-{n}", out)
                finally:
                    if backup.exists():
                        shutil.move(backup, target)


    def test_deleted_alias_fails(self):
        import shutil
        for n in NAMES:
            with self.subTest(skill=n):
                alias_dir = self.repo / "skills" / n
                backup = self.repo / f"alias-backup-{n}"
                shutil.move(alias_dir, backup)
                try:
                    code, out = self.validate()
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"skills/{n}", out)
                finally:
                    shutil.move(backup, alias_dir)

if __name__ == "__main__":
    unittest.main()
