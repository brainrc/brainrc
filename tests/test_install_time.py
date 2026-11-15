"""Install-time check (#279): scripts/check_install_time.py and the install-time workflow."""
import contextlib
import importlib.util
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import rmtree, stub_command  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_install_time", REPO / "scripts" / "check_install_time.py")
cit = importlib.util.module_from_spec(spec)
sys.modules["check_install_time"] = cit
spec.loader.exec_module(cit)

STATUS = """import os, sys, time
time.sleep(float(os.environ.get("STUB_SLEEP", "0")))
print("CREATE    claude    ~/.claude/skills/x")
print()
print("Dry run. Run `apply` to write.")
sys.exit(int(os.environ.get("STUB_EXIT", "0")))"""


class LocalFormulaTest(unittest.TestCase):
    def test_points_the_release_formula_at_the_local_sdist(self):
        d = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, d, True)
        sdist = d / "brainrc-1.2.3.tar.gz"
        sdist.write_bytes(b"sdist")
        text = cit.local_formula(sdist)
        self.assertIn(f'url "{sdist.as_uri()}"', text)
        self.assertIn(f'sha256 "{cit.sha256_of(sdist)}"', text)
        self.assertNotIn("local.invalid", text)


@unittest.skipIf(os.name == "nt", "the routes run from bash with POSIX stand-ins")
class RouteTest(unittest.TestCase):
    def setUp(self):
        self.stubs = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, self.stubs, True)
        self.dist = self.stubs / "dist"
        self.dist.mkdir()
        # PATH holds only bash and the stand-ins, so a runner's own uv or pipx can't answer.
        os.symlink(shutil.which("bash"), self.stubs / "bash")
        patcher = mock.patch.dict(os.environ, {"PATH": str(self.stubs), "STUB_EXIT": "0", "STUB_SLEEP": "0"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_fast_route_passes(self):
        stub_command(str(self.stubs), "uvx", STATUS)
        result, detail = cit.run_route("uvx", self.dist, 60)
        self.assertEqual(result, "PASS", detail)
        self.assertRegex(detail, r"^\d+\.\d s to first status$")

    def test_a_slow_route_fails(self):
        stub_command(str(self.stubs), "uvx", STATUS)
        os.environ["STUB_SLEEP"] = "0.3"
        result, detail = cit.run_route("uvx", self.dist, 0.1)
        self.assertEqual(result, "FAIL")
        self.assertIn("over the 0 s limit", detail)

    def test_a_failing_install_or_missing_status_line_fails(self):
        stub_command(str(self.stubs), "uvx", STATUS)
        os.environ["STUB_EXIT"] = "2"
        self.assertEqual(cit.run_route("uvx", self.dist, 60)[0], "FAIL")
        stub_command(str(self.stubs), "uvx", "print('something else')")
        self.assertEqual(cit.run_route("uvx", self.dist, 60)[0], "FAIL")

    def test_pipx_installs_then_runs_the_command_from_local_bin(self):
        stub_command(str(self.stubs), "pipx", "import os\n"
                     "d = os.path.join(os.environ['HOME'], '.local', 'bin'); os.makedirs(d)\n"
                     f"open(os.path.join(d, 'brainrc'), 'w').write('#!{sys.executable}\\n' + {STATUS!r})\n"
                     "os.chmod(os.path.join(d, 'brainrc'), 0o755)")
        result, detail = cit.run_route("pipx", self.dist, 60)
        self.assertEqual(result, "PASS", detail)

    def test_the_route_runs_offline_on_the_local_build_in_a_fresh_home(self):
        stub_command(str(self.stubs), "uvx", "import json, os\n"
                     "print(json.dumps({k: os.environ.get(k) for k in "
                     "('UV_FIND_LINKS', 'UV_OFFLINE', 'PIP_NO_INDEX', 'HOME', 'UV_CACHE_DIR')}))\n"
                     "print('Dry run. Run `apply` to write.')")
        os.environ["UV_CACHE_DIR"] = "/somewhere/else"
        script, extra = cit.plan("uvx", self.dist, self.stubs)
        self.assertEqual(script, "uvx brainrc status")
        self.assertEqual(extra["UV_FIND_LINKS"], str(self.dist))
        self.assertEqual((extra["UV_OFFLINE"], extra["PIP_NO_INDEX"]), ("1", "1"))
        self.assertIn("UV_CACHE_DIR", cit.ENV_DROP)

    def test_a_missing_tool_is_a_skip_not_a_pass(self):
        result, detail = cit.run_route("uvx", self.dist, 60)
        self.assertEqual((result, detail), ("SKIP", "uvx not installed"))
        with mock.patch.object(cit, "find_brew", return_value=None):
            self.assertEqual(cit.run_route("brew", self.dist, 60), ("SKIP", "Homebrew not installed"))

    def test_published_routes_skip_until_their_source_exists(self):
        for tool in ("uvx", "npx"):
            stub_command(str(self.stubs), tool, STATUS)
        with mock.patch.object(cit, "quiet", return_value=False):
            self.assertEqual(cit.run_route("uvx", None, 60), ("SKIP", "brainrc is not on PyPI yet"))
        with mock.patch.object(cit, "public", return_value=False):
            self.assertEqual(cit.run_route("npx", None, 60),
                             ("SKIP", "github.com/brainrc/brainrc is not public"))
        with mock.patch.object(cit, "find_brew", return_value=str(self.stubs / "brew")), \
                mock.patch.object(cit, "public", return_value=False):
            self.assertEqual(cit.run_route("brew", None, 60),
                             ("SKIP", "the brainrc/homebrew-tap tap doesn't exist yet"))

    def test_main_prints_one_line_per_route_and_fails_on_any_fail(self):
        stub_command(str(self.stubs), "uvx", STATUS)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cit.main(["--path", "uvx", "--path", "pipx", "--local", str(self.dist)])
        self.assertEqual(code, 0, out.getvalue())
        self.assertRegex(out.getvalue(), r"(?m)^PASS uvx: .*\n^SKIP pipx: pipx not installed$")
        os.environ["STUB_EXIT"] = "1"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cit.main(["--path", "uvx", "--local", str(self.dist)]), 1)


class WorkflowTest(unittest.TestCase):
    text = (REPO / ".github" / "workflows" / "install-time.yml").read_text()

    def test_every_route_on_ubuntu_and_macos(self):
        self.assertIn("os: [ubuntu-latest, macos-latest]", self.text)
        self.assertIn("route: [uvx, pipx, npx, brew]", self.text)
        self.assertEqual(cit.PATHS, ("uvx", "pipx", "npx", "brew"))

    def test_prs_time_the_local_build_and_the_schedule_times_what_is_published(self):
        self.assertRegex(self.text, r"(?m)^  pull_request:")
        self.assertIn("schedule:", self.text)
        self.assertIn("--local \"$RUNNER_TEMP/dist\"", self.text)
        self.assertIn("--published", self.text)
        self.assertIn("github.event_name == 'schedule'", self.text)

    def test_the_default_limit_is_sixty_seconds(self):
        self.assertNotIn("--limit", self.text)
        self.assertTrue(re.search(r'"--limit", type=float, default=60\.0',
                                  (REPO / "scripts" / "check_install_time.py").read_text()))


if __name__ == "__main__":
    unittest.main()
