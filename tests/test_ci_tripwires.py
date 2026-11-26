"""Tests for scripts/ci_tripwires.py: local tripwires in CI from a secret, never printed (#344)."""
import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
import uuid
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("ci_tripwires", REPO / "scripts" / "ci_tripwires.py")
ci_tripwires = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_tripwires)


def nowhere() -> str:
    """A term no tracked file holds, this one included."""
    return "zz-" + uuid.uuid4().hex


def run_main(env: dict) -> tuple[int, str]:
    buf = io.StringIO()
    with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(buf):
        code = ci_tripwires.main()
    return code, buf.getvalue()


class CiTripwiresTest(unittest.TestCase):
    def test_terms_are_written_as_valid_toml(self):
        terms = ['a"b', "back\\slash", "tab\there", "del\x7f", "ünïcode Café", "😀"]
        text = "terms = [" + ", ".join(ci_tripwires.toml_string(t) for t in terms) + "]\n"
        self.assertEqual(tomllib.loads(text)["terms"], terms)

    def test_a_pr_without_secrets_skips_with_a_notice(self):
        code, out = run_main({"NO_SECRETS": "true", "TRIPWIRE_TERMS": ""})
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("::notice::Local tripwires skipped"), out)

    def test_an_unset_secret_skips_with_a_notice(self):
        for value in ("", "  \n\n "):
            code, out = run_main({"NO_SECRETS": "false", "TRIPWIRE_TERMS": value})
            self.assertEqual(code, 0, out)
            self.assertTrue(out.startswith("::notice::Local tripwires skipped: the TRIPWIRE_TERMS"), out)
            self.assertNotIn("::error::", out)

    def test_every_term_is_masked_in_the_usual_spellings(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ci_tripwires.mask("Initech Corp")
        masks = {line.removeprefix("::add-mask::") for line in buf.getvalue().splitlines()}
        self.assertTrue({"Initech Corp", "initech corp", "INITECH CORP"} <= masks, masks)

    def test_end_to_end_a_match_fails_without_printing_the_term(self):
        """Against this checkout: one term only in file contents, one also in file names."""
        if subprocess.run(["git", "-C", str(REPO), "ls-files", "--error-unmatch", "CODE_OF_CONDUCT.md"],
                          capture_output=True).returncode:
            self.skipTest("needs a git checkout")
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(BRAINRC_HOME=str(Path(tmp) / "home"), RUNNER_TEMP=tmp, NO_SECRETS="false",
                   TRIPWIRE_TERMS=f"{nowhere()}\nContributor Covenant\ncode_of_conduct\n")
        out = subprocess.run([sys.executable, str(REPO / "scripts/ci_tripwires.py")], env=env,
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 1, out.stdout + out.stderr)
        shown = "\n".join(line for line in (out.stdout + out.stderr).splitlines()
                          if not line.startswith("::add-mask::"))
        self.assertIn("local tripwire #2", shown)
        self.assertIn("***.md: local tripwire #3 in the file name", shown)
        self.assertNotIn("contributor covenant", shown.casefold())
        self.assertNotIn("code_of_conduct", shown.casefold())
        self.assertEqual(list(Path(tmp).rglob("*.toml")), [], "the terms file must be removed")

    def test_end_to_end_no_match_passes(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(BRAINRC_HOME=str(Path(tmp) / "home"), RUNNER_TEMP=tmp, NO_SECRETS="false",
                   TRIPWIRE_TERMS=nowhere())
        out = subprocess.run([sys.executable, str(REPO / "scripts/ci_tripwires.py")], env=env,
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
