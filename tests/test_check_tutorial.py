"""Tests for scripts/check_tutorial.py: parsing, doc coupling, and an end-to-end run."""
import contextlib
import importlib.util
import io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "tutorial.md"

spec = importlib.util.spec_from_file_location("check_tutorial", REPO / "scripts" / "check_tutorial.py")
check_tutorial = importlib.util.module_from_spec(spec)
sys.modules["check_tutorial"] = check_tutorial
spec.loader.exec_module(check_tutorial)


sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import default_pack_env  # noqa: E402
from support import rmtree


def setUpModule():
    """The tutorial's `apply` fetches the default pack: serve it from the offline stand-in."""
    env = default_pack_env()
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    unittest.addModuleCleanup(lambda: [os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
                                       for k, v in old.items()])


def run_main(args: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = check_tutorial.main(args)
    return code, out.getvalue()


class StepsTest(unittest.TestCase):
    def test_real_doc_has_steps_1_to_5(self):
        found = check_tutorial.steps(DOC.read_text(encoding="utf-8"))
        self.assertEqual(sorted(found), [1, 2, 3, 4, 5])

    def test_step_blocks_come_from_the_doc(self):
        found = check_tutorial.steps(DOC.read_text(encoding="utf-8"))
        self.assertIn("pack.toml", found[2])
        self.assertIn("validate --pack", found[4])
        self.assertNotIn("git clone", found[1])
        self.assertIn("scripts/brainrc.py validate", found[1])

    def test_missing_step_fails(self):
        text = DOC.read_text(encoding="utf-8").replace("## 4. Validate the pack", "## 9. Validate the pack")
        with self.assertRaises(ValueError) as cm:
            check_tutorial.steps(text)
        self.assertIn("4", str(cm.exception))


class DocCouplingTest(unittest.TestCase):
    """AC6: the commands come from the doc, so editing the doc changes the result."""

    def edited(self, old: str, new: str) -> str:
        text = DOC.read_text(encoding="utf-8")
        self.assertIn(old, text)
        d = tempfile.mkdtemp(prefix="tut-test-")
        self.addCleanup(rmtree, d, True)
        p = Path(d, "tutorial.md")
        p.write_text(text.replace(old, new), encoding="utf-8")
        return str(p)

    def test_changed_command_fails_naming_step(self):
        code, out = run_main(["--doc", self.edited("validate --pack", "validate --pak")])
        self.assertEqual(code, 1)
        self.assertIn("step 4", out)

    def test_changed_heading_fails_parsing(self):
        code, out = run_main(["--doc", self.edited("## 4. Validate the pack", "## 9. Validate the pack")])
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)

    def test_missing_documented_output_fails(self):
        code, out = run_main(["--doc", self.edited("| grep 'Everything in sync.'", "| grep 'Everything in sync.' >/dev/null; echo hi")])
        self.assertEqual(code, 1)
        self.assertIn("step 5", out)


class EndToEndTest(unittest.TestCase):
    """AC5: the real tutorial passes, without writing to the real checkout or HOME."""

    def test_real_doc_passes_and_stays_sandboxed(self):
        local = REPO / "packs.local.toml"
        existed = local.exists()
        with tempfile.TemporaryDirectory(prefix="tut-home-") as fake_home:
            old = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
            os.environ["HOME"] = os.environ["USERPROFILE"] = fake_home
            try:
                code, out = run_main([])
            finally:
                for k, v in old.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            self.assertEqual(code, 0, out)
            for n in (1, 2, 3, 4, 5):
                self.assertIn(f"PASS step {n}", out)
            self.assertEqual(os.listdir(fake_home), [], "script wrote into the caller's HOME")
        self.assertEqual(local.exists(), existed, "script wrote packs.local.toml into the real checkout")


README_FIXTURE = """# brainrc

## Quickstart

```bash
git clone https://example.invalid/brainrc.git ~/brainrc
python3 scripts/brainrc.py status
python3 scripts/brainrc.py apply
python3 scripts/brainrc.py status
```

## Install

```bash
echo not-the-quickstart
```
"""


class ReadmeParseTest(unittest.TestCase):
    def test_first_bash_block_under_quickstart_without_clone(self):
        found = check_tutorial.parse_readme(README_FIXTURE)
        self.assertEqual(list(found), [1])
        title, block = found[1]
        self.assertEqual(title, "quickstart")
        self.assertNotIn("git clone", block)
        self.assertEqual(block.count("scripts/brainrc.py"), 3)
        self.assertNotIn("not-the-quickstart", block)

    def test_missing_section_raises(self):
        with self.assertRaises(ValueError):
            check_tutorial.parse_readme(README_FIXTURE.replace("## Quickstart", "## Start"))

    def test_section_without_bash_block_raises(self):
        with self.assertRaises(ValueError):
            check_tutorial.parse_readme(README_FIXTURE.replace("```bash", "```text", 1))

    def test_expected_patterns_are_stable_lines(self):
        self.assertEqual(check_tutorial.EXPECTED_README[1],
                         [re.escape("Dry run. Run `apply` to write."), re.escape("Everything in sync.")])


class ReadmeCheckTest(unittest.TestCase):
    def readme(self, text: str) -> str:
        d = tempfile.mkdtemp(prefix="readme-test-")
        self.addCleanup(rmtree, d, True)
        p = Path(d, "README.md")
        p.write_text(text, encoding="utf-8")
        return str(p)

    def run_readme(self, text: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory(prefix="readme-home-") as fake_home:
            old = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
            os.environ["HOME"] = os.environ["USERPROFILE"] = fake_home
            try:
                code, out = run_main(["--readme", self.readme(text)])
            finally:
                for k, v in old.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            self.assertEqual(os.listdir(fake_home), [], "script wrote into the caller's HOME")
        return code, out

    def test_fixture_passes(self):
        code, out = self.run_readme(README_FIXTURE)
        self.assertEqual(code, 0, out)
        self.assertIn("PASS step 1 quickstart", out)

    def test_broken_command_fails(self):
        code, out = self.run_readme(README_FIXTURE.replace("apply", "aply"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL step 1 quickstart", out)

    def test_missing_documented_output_fails(self):
        code, out = self.run_readme(README_FIXTURE.replace("python3 scripts/brainrc.py status\n```", "echo done\n```"))
        self.assertEqual(code, 1)
        self.assertIn("output missing", out)

    def test_missing_section_is_a_fail_line(self):
        code, out = self.run_readme("# brainrc\n")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", out)

    def test_real_readme_passes_and_stays_sandboxed(self):
        code, out = self.run_readme((REPO / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(code, 0, out)
        self.assertIn("PASS step 1 quickstart", out)


class RealReadmeTest(unittest.TestCase):
    """AC4/AC5/AC9: the checked patterns appear in the README transcript, which leaks nothing."""
    text = (REPO / "README.md").read_text(encoding="utf-8")

    def test_expected_output_is_shown_in_the_readme(self):
        for pattern in check_tutorial.EXPECTED_README[1]:
            self.assertRegex(self.text, pattern)

    def test_quickstart_commands_are_status_apply_status(self):
        block = check_tutorial.parse_readme(self.text)[1][1]
        cmds = [l for l in block.splitlines() if "scripts/brainrc.py" in l]
        self.assertEqual([c.split()[-1] for c in cmds], ["status", "apply", "status"])

    def test_no_absolute_home_paths_or_emails(self):
        for bad in ("/home/", "/Users/", "/root/"):
            self.assertNotIn(bad, self.text)
        self.assertIsNone(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", self.text))

    def test_at_most_100_lines(self):
        self.assertLessEqual(len(self.text.splitlines()), 100)

    def test_lead_precedes_spec_agent_and_names_five_tools(self):
        lead = " ".join(self.text.split("\n## ", 1)[0].split())
        for name in ("Claude Code", "Codex CLI", "OpenCode", "Antigravity CLI", "Cursor"):
            self.assertIn(name, lead)
        self.assertIn("docs/formats.md#harness-support", lead)
        self.assertLess(self.text.index("Quickstart"), self.text.index("## spec-agent"))
        self.assertLess(self.text.index("## Install"), self.text.index("## spec-agent"))


if __name__ == "__main__":
    unittest.main()
