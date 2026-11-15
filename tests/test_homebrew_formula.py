"""Homebrew tap (#277): scripts/homebrew_formula.py and release.yml's `homebrew` job."""
import contextlib
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location("homebrew_formula", REPO / "scripts" / "homebrew_formula.py")
hf = importlib.util.module_from_spec(spec)
sys.modules["homebrew_formula"] = hf
spec.loader.exec_module(hf)

SHA = "a" * 64
URL = "https://files.pythonhosted.org/packages/ab/cd/brainrc-1.2.3.tar.gz"


def job(text: str, name: str) -> str:
    m = re.search(rf"^  {re.escape(name)}:\n(.*?)(?=^  \S|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def listing(sha256=SHA, url=URL):
    return {"urls": [{"packagetype": "bdist_wheel", "url": "https://x/y.whl", "digests": {"sha256": "b" * 64}},
                     {"packagetype": "sdist", "url": url, "digests": {"sha256": sha256}}]}


class RenderTest(unittest.TestCase):
    def test_formula_names_the_url_sha_and_python_and_has_no_resources(self):
        text = hf.render("1.2.3", URL, SHA)
        self.assertIn(f'url "{URL}"', text)
        self.assertIn(f'sha256 "{SHA}"', text)
        self.assertIn('depends_on "python@3.13"', text)
        self.assertIn("virtualenv_install_with_resources", text)
        self.assertNotIn("resource ", text)
        self.assertIn('"brainrc #{version}"', text)
        self.assertIn("class Brainrc < Formula", text)
        self.assertIn("brainrc apply --repair", text)  # caveats: links break on upgrade

    def test_bad_inputs_are_refused(self):
        for url, sha in (("http://x/brainrc-1.2.3.tar.gz", SHA), ('https://x/"brainrc-1.2.3.tar.gz', SHA),
                         ("https://x/brainrc-9.9.9.tar.gz", SHA), (URL, "abc"),
                         ("https://x/#{system('id')}/brainrc-1.2.3.tar.gz", SHA)):
            with self.assertRaises(hf.FormulaError, msg=url):
                hf.render("1.2.3", url, sha)

    def test_version_comes_from_the_sdist_name(self):
        self.assertEqual(hf.version_of(Path("brainrc-0.9.1.tar.gz")), "0.9.1")
        with self.assertRaises(hf.FormulaError):
            hf.version_of(Path("other-0.9.1.tar.gz"))

    @unittest.skipUnless(shutil.which("ruby"), "ruby not installed")
    def test_formula_is_valid_ruby(self):
        with tempfile.NamedTemporaryFile("w", suffix=".rb", delete=False) as f:
            f.write(hf.render("1.2.3", URL, SHA))
        self.addCleanup(Path(f.name).unlink)
        r = subprocess.run(["ruby", "-c", f.name], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


class PypiUrlTest(unittest.TestCase):
    def test_uses_pypis_sdist_url_when_the_sha_matches(self):
        self.assertEqual(hf.pypi_url(listing(), "1.2.3", SHA), URL)

    def test_a_different_sha_on_pypi_fails(self):
        with self.assertRaisesRegex(hf.ShaMismatch, "has sha256 c+, the release built a+"):
            hf.pypi_url(listing(sha256="c" * 64), "1.2.3", SHA)

    def test_odd_json_shapes_are_format_errors(self):
        for odd in ([], {"info": None, "urls": None}, {"urls": [{"packagetype": "sdist", "digests": None}]},
                    {"urls": [{"packagetype": "sdist", "digests": {"sha256": SHA}}]}):
            with self.assertRaises(hf.FormulaError, msg=odd):
                hf.pypi_url(odd, "1.2.3", SHA)

    def test_no_sdist_or_another_version_fails(self):
        with self.assertRaisesRegex(hf.FormulaError, "lists no sdist"):
            hf.pypi_url({"urls": []}, "1.2.3", SHA)
        with self.assertRaisesRegex(hf.FormulaError, "is for 1.2.2"):
            hf.pypi_url({**listing(), "info": {"version": "1.2.2"}}, "1.2.3", SHA)

    def test_main_reads_the_json_and_writes_pypis_url(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        sdist = d / "brainrc-1.2.3.tar.gz"
        sdist.write_bytes(b"sdist")
        sha = hashlib.sha256(b"sdist").hexdigest()
        (d / "pypi.json").write_text(json.dumps(listing(sha256=sha)))
        out = d / "brainrc.rb"
        self.assertEqual(hf.main([str(sdist), "--pypi-json", str(d / "pypi.json"), "--out", str(out)]), 0)
        self.assertIn(f'url "{URL}"', out.read_text())
        (d / "pypi.json").write_text("not json")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(hf.main([str(sdist), "--pypi-json", str(d / "pypi.json")]), 1)
        self.assertIn("ERROR", err.getvalue())
        (d / "pypi.json").write_text(json.dumps(listing(sha256="c" * 64)))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(hf.main([str(sdist), "--pypi-json", str(d / "pypi.json")]), 3)


class MainTest(unittest.TestCase):
    def test_writes_the_formula_for_an_sdist(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        sdist = d / "brainrc-1.2.3.tar.gz"
        sdist.write_bytes(b"sdist")
        out = d / "tap" / "Formula" / "brainrc.rb"
        self.assertEqual(hf.main([str(sdist), "--out", str(out)]), 0)
        text = out.read_text()
        self.assertIn(f'sha256 "{hashlib.sha256(b"sdist").hexdigest()}"', text)
        self.assertIn('url "https://files.pythonhosted.org/packages/source/b/brainrc/brainrc-1.2.3.tar.gz"', text)

    def test_a_missing_sdist_is_an_error_line(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(hf.main(["/nonexistent/brainrc-1.2.3.tar.gz"]), 1)
        self.assertIn("ERROR", err.getvalue())


class HomebrewJobTest(unittest.TestCase):
    text = (REPO / ".github" / "workflows" / "release.yml").read_text()
    brew = job(text, "homebrew")

    def test_runs_after_pypi_publishing(self):
        self.assertIn("needs: [release, dist, pypi]", self.brew)

    def test_skips_with_a_notice_without_the_token(self):
        self.assertIn("secrets.HOMEBREW_TAP_TOKEN", self.brew)
        self.assertNotIn("DEPLOY_KEY", self.text)
        self.assertIn("::notice title=Homebrew tap not updated::", self.brew)
        self.assertNotRegex(self.brew, r"if: .*secrets\.")  # secrets can't gate `if:`; the step output does
        steps = self.brew.split("      - ")[2:]
        self.assertTrue(all("if: steps.key.outputs.present == 'true'" in s for s in steps), steps)

    def test_pushes_over_https_with_the_token_kept_out_of_urls_and_config(self):
        self.assertIn('git clone --depth 1 "https://github.com/${TAP}.git"', self.brew)
        self.assertIn('GIT_CONFIG_KEY_0: credential.helper\n          GIT_CONFIG_VALUE_0: ""', self.brew)
        self.assertIn("GIT_CONFIG_KEY_1: credential.helper", self.brew)
        self.assertIn('test "$1" = get || exit 0', self.brew)
        self.assertIn('password=${TAP_TOKEN}', self.brew)
        self.assertNotRegex(self.brew, r"https://[^/\s\"]*@github\.com")  # no token in a URL
        self.assertNotIn("git config credential", self.brew)  # nothing written to .git/config
        self.assertNotIn("ssh", self.brew)
        self.assertIn("TAP: brainrc/homebrew-tap", self.brew)
        self.assertIn("--pypi-json", self.brew)
        self.assertNotIn("id-token", self.brew)

    def test_a_sha_mismatch_is_not_retried_and_brew_tests_the_formula_before_the_push(self):
        self.assertIn('[ "$rc" -eq 3 ] && exit 1', self.brew)
        self.assertLess(self.brew.index("brew test "), self.brew.index("git push"))


if __name__ == "__main__":
    unittest.main()
