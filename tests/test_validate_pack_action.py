"""The validate-pack action and pre-commit hook (#139) that a pack's own CI uses. No YAML parser in
the stdlib, so these read the files as text."""
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTION = ROOT / ".github/actions/validate-pack/action.yml"
HOOKS = ROOT / ".pre-commit-hooks.yaml"
WORKFLOW = ROOT / ".github/workflows/validate.yml"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ActionTest(unittest.TestCase):
    def test_a_composite_action_with_its_inputs(self):
        action = text(ACTION)
        self.assertIn("using: composite", action)
        for name, default in (("path", '"."'), ("default-packs", '"true"'), ("python-version", '"3.12"')):
            with self.subTest(input=name):
                self.assertRegex(action, rf"\n  {name}:\n(    .*\n)*?    default: {re.escape(default)}\n")

    def test_it_runs_the_core_it_is_pinned_to(self):
        action = text(ACTION)
        self.assertEqual(action.count("CORE: ${{ github.action_path }}/../../.."), 2)
        self.assertTrue((ACTION.parent / "../../../scripts/brainrc.py").resolve().is_file())
        self.assertIn('python "$CORE/scripts/brainrc.py" validate --pack "$PACK"', action)
        self.assertIn('python "$CORE/scripts/brainrc.py" apply', action)

    def test_inputs_reach_the_shell_only_through_env(self):
        # `${{ inputs.x }}` inside run: would be pasted into the script; env keeps it a value.
        runs = re.findall(r"run: \|\n((?:        .*\n)+)", text(ACTION))
        self.assertEqual(len(runs), 2)
        for script in runs:
            self.assertNotIn("${{", script)

    def test_it_writes_to_a_home_of_its_own(self):
        action = text(ACTION)
        self.assertEqual(action.count('HOME="$WORK/home" USERPROFILE="$WORK/home" BRAINRC_HOME="$WORK/settings"'), 2)
        self.assertIn("WORK: ${{ runner.temp }}/brainrc-validate-pack", action)

    def test_actions_it_uses_are_pinned_like_cores_ci(self):
        uses = re.findall(r"uses: (\S+) # (\S+)", text(ACTION))
        self.assertEqual(len(uses), 1)
        self.assertIn(f"uses: {uses[0][0]} # {uses[0][1]}", text(WORKFLOW))
        self.assertRegex(uses[0][0], r"@[0-9a-f]{40}$")

    def test_cores_ci_checks_both_example_packs_with_it(self):
        workflow = text(WORKFLOW)
        self.assertEqual(workflow.count("uses: ./.github/actions/validate-pack"), 2)
        for pack in ("examples/pack-acme", "examples/pack-homelab"):
            self.assertIn(f"path: {pack}", workflow)


class PreCommitHookTest(unittest.TestCase):
    def test_the_hook_runs_the_installed_console_script(self):
        hooks = text(HOOKS)
        self.assertIn("- id: brainrc-validate-pack", hooks)
        self.assertIn("entry: brainrc validate --pack .", hooks)
        self.assertIn("language: python", hooks)
        self.assertIn("pass_filenames: false", hooks)
        scripts = tomllib.loads(text(ROOT / "pyproject.toml"))["project"]["scripts"]
        self.assertIn("brainrc", scripts)


class DocsTest(unittest.TestCase):
    def test_docs_and_the_acme_example_show_both(self):
        docs = text(ROOT / "docs/packs.md")
        readme = text(ROOT / "examples/pack-acme/README.md")
        self.assertTrue("uses: brainrc/brainrc/.github/actions/validate-pack@" in docs)
        self.assertTrue("id: brainrc-validate-pack" in docs)
        self.assertTrue("uses: brainrc/brainrc/.github/actions/validate-pack@" in readme)


if __name__ == "__main__":
    unittest.main()
