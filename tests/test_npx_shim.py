"""npx shim (#278): the generated package.json and bin/brainrc.js, run with node where it exists."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brainrc  # noqa: E402
from support import rmtree, stub_command  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
VERSION = (REPO / "VERSION").read_text().strip()
NODE = shutil.which("node")
# Records its arguments and exits with the code in STUB_EXIT.
RECORDER = """import json, os, sys
with open(os.environ["STUB_LOG"], "w") as f:
    json.dump(sys.argv[1:], f)
sys.exit(int(os.environ.get("STUB_EXIT", "0")))"""


class PackageJsonTest(unittest.TestCase):
    def test_committed_package_json_is_current_and_matches_version(self):
        manifests = brainrc.plugin_manifests()
        self.assertEqual((REPO / "package.json").read_text(), manifests["package.json"])
        pkg = json.loads(manifests["package.json"])
        self.assertEqual(pkg["version"], VERSION)
        self.assertEqual(pkg["bin"], {"brainrc": "bin/brainrc.js"})
        self.assertTrue(pkg["private"], "brainrc is not published to npm")
        self.assertEqual(sorted(pkg["files"]), ["VERSION", "bin/brainrc.js"])
        self.assertNotIn("dependencies", pkg)
        self.assertNotIn("scripts", pkg)  # no install scripts run on a user's machine

    def test_a_stale_package_json_fails_validation(self):
        old = brainrc.config.REPO
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, tmp, True)
        for name in (".claude-plugin", ".cursor-plugin", "overrides", "bin"):
            shutil.copytree(REPO / name, tmp / name)
        for name in ("VERSION", "plugin.json", "package.json"):
            shutil.copy2(REPO / name, tmp / name)
        brainrc.config.REPO = tmp
        try:
            self.assertEqual(brainrc.check_plugin(), [])
            (tmp / "VERSION").write_text("9.9.9\n")
            errors = brainrc.check_plugin()
        finally:
            brainrc.config.REPO = old
        self.assertTrue(any(e.startswith("package.json: stale") for e in errors), errors)

    def test_release_commits_package_json(self):
        release = (REPO / ".github" / "workflows" / "release.yml").read_text()
        self.assertIn(".cursor-plugin plugin.json package.json", release)


@unittest.skipUnless(NODE, "node not installed")
@unittest.skipIf(os.name == "nt", "node finds uvx.exe, not the .cmd stand-in")
class ShimTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, self.root, True)
        (self.root / "bin").mkdir()
        shutil.copy2(REPO / "bin" / "brainrc.js", self.root / "bin" / "brainrc.js")
        shutil.copy2(REPO / "VERSION", self.root / "VERSION")
        shutil.copy2(REPO / "package.json", self.root / "package.json")
        self.bin_dir = self.root / "stubs"
        self.bin_dir.mkdir()
        self.log = self.root / "args.json"

    def run_shim(self, *args, path=None, exit_code="0"):
        env = {**os.environ, "STUB_LOG": str(self.log), "STUB_EXIT": exit_code,
               "PATH": path if path is not None else os.pathsep.join([str(self.bin_dir), os.environ["PATH"]])}
        return subprocess.run([NODE, str(self.root / "bin" / "brainrc.js"), *args], env=env,
                              capture_output=True, text=True, timeout=60)

    def test_runs_uvx_pinned_to_version_and_passes_arguments_and_exit_code(self):
        stub_command(str(self.bin_dir), "uvx", RECORDER)
        r = self.run_shim("status", "--only", "claude", exit_code="3")
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertEqual(json.loads(self.log.read_text()), [f"brainrc@{VERSION}", "status", "--only", "claude"])

    def test_without_uv_it_says_how_to_get_it(self):
        node_only = str(self.root / "node-only")
        os.mkdir(node_only)
        r = self.run_shim("status", path=node_only)
        self.assertEqual(r.returncode, 127)
        self.assertIn("isn't on PATH", r.stderr)
        self.assertIn("https://docs.astral.sh/uv/", r.stderr)

    def test_a_version_mismatch_stops_before_running_anything(self):
        stub_command(str(self.bin_dir), "uvx", RECORDER)
        (self.root / "VERSION").write_text("9.9.9\n")
        r = self.run_shim("status")
        self.assertEqual(r.returncode, 1)
        self.assertIn("VERSION says 9.9.9", r.stderr)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
