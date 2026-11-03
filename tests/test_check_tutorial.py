"""Tests for scripts/check_tutorial.py: parsing, doc coupling, and an end-to-end run."""
import contextlib
import importlib.util
import io
import os
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
        self.addCleanup(__import__("shutil").rmtree, d, True)
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


if __name__ == "__main__":
    unittest.main()
