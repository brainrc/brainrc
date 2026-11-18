"""PyPI publishing (#108): scripts/check_dist.py, the sdist's contents, and release.yml's jobs."""
import contextlib
import importlib.util
import io
import re
import shutil
import sys
import tarfile
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO / ".github" / "workflows"
VERSION = (REPO / "VERSION").read_text().strip()

spec = importlib.util.spec_from_file_location("check_dist", REPO / "scripts" / "check_dist.py")
check_dist = importlib.util.module_from_spec(spec)
sys.modules["check_dist"] = check_dist
spec.loader.exec_module(check_dist)

CORE = check_dist.force_include()
METADATA = f"Metadata-Version: 2.4\nName: brainrc\nVersion: {VERSION}\nRequires-Python: >=3.11\n"


def job(text: str, name: str) -> str:
    """The text of one job in a workflow: from `  <name>:` to the next top-level job."""
    m = re.search(rf"^  {re.escape(name)}:\n(.*?)(?=^  \S|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


class CheckDistTest(unittest.TestCase):
    def make(self, sdist_extra=(), metadata=METADATA, skip_core=False, skip_templates=False) -> Path:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        root = f"brainrc-{VERSION}"
        with tarfile.open(d / f"{root}.tar.gz", "w:gz") as tf:
            for rel in [*([] if skip_core else CORE), "brainrc/cli.py", *sdist_extra]:
                data = b"x"
                info = tarfile.TarInfo(f"{root}/{rel}")
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        with zipfile.ZipFile(d / f"{root}-py3-none-any.whl", "w") as zf:
            zf.writestr(f"{root}.dist-info/METADATA", metadata)
            for dest in [*CORE.values(), *([] if skip_templates else check_dist.templates())]:
                zf.writestr(dest, "x")
        return d

    def run_main(self, dist: Path) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_dist.main([str(dist)])
        return code, out.getvalue()

    def test_a_good_dist_passes_and_prints_hashes(self):
        code, out = self.run_main(self.make())
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)
        self.assertIn(f"brainrc-{VERSION}.tar.gz", out)
        self.assertRegex(out, r"sha256 [0-9a-f]{64}  brainrc-")

    def test_specs_or_tests_in_the_sdist_fail(self):
        code, out = self.run_main(self.make(sdist_extra=["specs/x/spec.md", "tests/test_x.py"]))
        self.assertEqual(code, 1)
        self.assertIn("FAIL sdist leaves out specs, tests and tooling: has ['specs', 'tests']", out)

    def test_an_sdist_without_core_fails(self):
        code, out = self.run_main(self.make(skip_core=True))
        self.assertEqual(code, 1)
        self.assertIn("FAIL sdist carries core", out)

    def test_a_wheel_without_the_new_pack_templates_fails(self):
        self.assertIn("brainrc/_templates/pack/dot-github/workflows/validate.yml", check_dist.templates())
        code, out = self.run_main(self.make(skip_templates=True))
        self.assertEqual(code, 1)
        self.assertIn("FAIL wheel carries the `new pack` templates", out)

    def test_a_dependency_or_another_version_fails(self):
        code, out = self.run_main(self.make(metadata=METADATA + "Requires-Dist: requests\n"))
        self.assertIn("FAIL wheel has no dependencies", out)
        self.assertEqual(code, 1)
        code, out = self.run_main(self.make(metadata=METADATA.replace(VERSION, "0.0.1")))
        self.assertIn("FAIL wheel version", out)
        self.assertEqual(code, 1)

    def test_a_look_alike_name_is_not_core(self):
        d = self.make()
        wheel = d / f"brainrc-{VERSION}-py3-none-any.whl"
        with zipfile.ZipFile(wheel) as zf:
            kept = {n: zf.read(n) for n in zf.namelist() if n != "brainrc/_core/VERSION"}
        with zipfile.ZipFile(wheel, "w") as zf:
            for n, data in kept.items():
                zf.writestr(n, data)
            zf.writestr("brainrc/_core/VERSION.bak", "x")
        code, out = self.run_main(d)
        self.assertEqual(code, 1)
        self.assertIn("FAIL wheel bundles core: missing ['brainrc/_core/VERSION']", out)

    def test_a_missing_dist_dir_is_a_fail_line(self):
        code, out = self.run_main(Path(tempfile.gettempdir()) / "no-such-dist-dir")
        self.assertEqual(code, 1)
        self.assertIn("FAIL files", out)

    def test_a_missing_or_extra_file_fails(self):
        d = self.make()
        (d / "stray.txt").write_text("x")
        code, out = self.run_main(d)
        self.assertEqual(code, 1)
        self.assertIn("FAIL files", out)


class SdistConfigTest(unittest.TestCase):
    def test_the_sdist_includes_every_wheel_force_include_source(self):
        hatch = tomllib.loads((REPO / "pyproject.toml").read_text())["tool"]["hatch"]["build"]["targets"]
        only = hatch["sdist"]["only-include"]
        for src in hatch["wheel"]["force-include"]:
            self.assertTrue(any(src == o or src.startswith(o + "/") for o in only), src)
        self.assertIn("brainrc", only)
        for src, dest in CORE.items():
            self.assertTrue((REPO / src).exists(), src)
            self.assertTrue(dest.startswith("brainrc/_core/"), dest)


class ReleaseWorkflowTest(unittest.TestCase):
    text = (WORKFLOWS / "release.yml").read_text()

    def test_every_action_is_pinned_to_a_commit(self):
        for wf in sorted(WORKFLOWS.glob("*.yml")):
            for line in wf.read_text().splitlines():
                m = re.match(r"\s*(?:- )?uses: (\S+)", line)
                if m and not m.group(1).startswith("./"):
                    self.assertRegex(m.group(1), r"@[0-9a-f]{40}$", f"{wf.name}: {line.strip()}")

    def test_pypi_publishes_by_trusted_publishing_from_environment_pypi(self):
        pypi = job(self.text, "pypi")
        self.assertIn("name: pypi\n", pypi)
        self.assertIn("id-token: write", pypi)
        self.assertIn("pypa/gh-action-pypi-publish@", pypi)
        self.assertIn("skip-existing: true", pypi)
        self.assertNotRegex(pypi, r"password|api[-_]?token|secrets\.")
        self.assertRegex(pypi, r"needs: \[release, dist\]")

    def test_only_the_publish_job_gets_an_oidc_token(self):
        for name in ("release", "dist", "attach"):
            self.assertNotIn("id-token", job(self.text, name), name)
        self.assertIn("contents: read", self.text.split("jobs:")[0])

    def test_dist_builds_from_the_tag_with_pinned_tools_and_no_write_token(self):
        dist = job(self.text, "dist")
        self.assertIn("ref: v${{ needs.release.outputs.version }}", dist)
        self.assertIn("persist-credentials: false", dist)
        self.assertIn("contents: read", dist)
        self.assertNotIn("contents: write", dist)
        self.assertIn("hatchling==", dist)
        self.assertIn("--no-isolation", dist)
        self.assertLess(dist.index("python3 -m build"), dist.index("scripts/check_dist.py"))

    def test_attach_only_uploads_the_checked_files(self):
        attach = job(self.text, "attach")
        self.assertIn("needs: [release, dist]", attach)
        self.assertIn("gh release upload", attach)
        self.assertNotIn("actions/checkout", attach)


if __name__ == "__main__":
    unittest.main()
