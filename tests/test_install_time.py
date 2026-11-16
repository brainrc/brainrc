"""Install-time check (#279): scripts/check_install_time.py and the install-time workflow."""
import contextlib
import importlib.util
import io
import json
import os
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


def setUpModule():
    # Under CI, main() would otherwise annotate and write these tests' made-up results into the
    # real job summary; ReportTest sets both back on its own.
    patcher = mock.patch.dict(os.environ)
    patcher.start()
    unittest.addModuleCleanup(patcher.stop)
    for key in ("GITHUB_ACTIONS", "GITHUB_STEP_SUMMARY"):
        os.environ.pop(key, None)


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

    def test_with_a_ceiling_a_slow_route_warns_up_to_it_and_fails_over_it(self):
        stub_command(str(self.stubs), "uvx", STATUS)
        os.environ["STUB_SLEEP"] = "0.3"
        result, detail = cit.run_route("uvx", self.dist, 0.1, ceiling=60)
        self.assertEqual(result, "WARN")
        self.assertIn("over the 0 s limit", detail)
        result, detail = cit.run_route("uvx", self.dist, 0.1, ceiling=0.2)
        self.assertEqual(result, "FAIL")
        self.assertIn("over the 0 s ceiling", detail)
        os.environ["STUB_EXIT"] = "1"  # a broken install fails under the ceiling too
        self.assertEqual(cit.run_route("uvx", self.dist, 0.1, ceiling=60)[0], "FAIL")

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
        (self.dist / f"brainrc-{cit.VERSION}-py3-none-any.whl").write_bytes(b"")
        result, detail = cit.run_route("pipx", self.dist, 60)
        self.assertEqual(result, "PASS", detail)
        script, extra, _ = cit.plan("pipx", self.dist, self.stubs)
        self.assertIn(f"pipx install '{self.dist}/brainrc-{cit.VERSION}-py3-none-any.whl'", script)
        self.assertEqual(extra, {})  # pipx fetches its own pip from the index

    def test_the_route_runs_offline_on_the_local_build_in_a_fresh_home(self):
        log = self.stubs / "env.json"
        stub_command(str(self.stubs), "uvx", "import json, os, sys\n"
                     f"json.dump({{'argv': sys.argv[1:], **{{k: os.environ.get(k) for k in "
                     "('UV_FIND_LINKS', 'UV_OFFLINE', 'PIP_NO_INDEX', 'HOME', 'UV_CACHE_DIR')}}, "
                     f"open({str(log)!r}, 'w'))\n"
                     "print('Dry run. Run `apply` to write.')")
        os.environ["UV_CACHE_DIR"] = "/somewhere/else"
        result, detail = cit.run_route("uvx", self.dist, 60)
        self.assertEqual(result, "PASS", detail)
        seen = json.loads(log.read_text())
        self.assertEqual(seen["argv"], ["brainrc", "status"])
        self.assertEqual(seen["UV_FIND_LINKS"], str(self.dist))
        self.assertEqual((seen["UV_OFFLINE"], seen["PIP_NO_INDEX"]), ("1", "1"))
        self.assertIsNone(seen["UV_CACHE_DIR"])  # the runner's warm cache is dropped
        self.assertTrue(seen["HOME"].endswith("/home") and seen["HOME"] != os.environ.get("HOME"))

    def test_a_missing_tool_is_a_skip_not_a_pass(self):
        result, detail = cit.run_route("uvx", self.dist, 60)
        self.assertEqual((result, detail), ("SKIP", "uvx not installed"))
        with mock.patch.object(cit, "find_brew", return_value=None):
            self.assertEqual(cit.run_route("brew", self.dist, 60), ("SKIP", "Homebrew not installed"))

    def test_published_routes_skip_until_their_source_exists(self):
        for tool in ("uvx", "npx"):
            stub_command(str(self.stubs), tool, STATUS)
        with mock.patch.object(cit, "on_pypi", side_effect=cit.Skip("brainrc is not on PyPI yet")):
            self.assertEqual(cit.run_route("uvx", None, 60), ("SKIP", "brainrc is not on PyPI yet"))
        with mock.patch.object(cit, "public", return_value=False):
            self.assertEqual(cit.run_route("npx", None, 60),
                             ("SKIP", "github.com/brainrc/brainrc is not public"))
        with mock.patch.object(cit, "find_brew", return_value=str(self.stubs / "brew")), \
                mock.patch.object(cit, "public", return_value=False):
            self.assertEqual(cit.run_route("brew", None, 60),
                             ("SKIP", "the brainrc/homebrew-tap tap doesn't exist yet"))

    def test_npx_also_needs_uv_for_the_shim(self):
        stub_command(str(self.stubs), "npx", STATUS)
        self.assertEqual(cit.run_route("npx", self.dist, 60), ("SKIP", "uvx not installed"))

    def test_published_npx_skips_until_pypi_has_the_repos_version(self):
        for tool in ("uvx", "npx"):
            stub_command(str(self.stubs), tool, STATUS)
        with mock.patch.object(cit, "public", return_value=True), \
                mock.patch.object(cit, "on_pypi", side_effect=cit.Skip("not yet")) as pypi:
            self.assertEqual(cit.run_route("npx", None, 60), ("SKIP", "not yet"))
        pypi.assert_called_once_with(cit.VERSION)

    def test_brew_skips_when_brainrc_is_already_installed_with_homebrew(self):
        stub_command(str(self.stubs), "brew", "import sys; sys.exit(0 if sys.argv[1] == 'list' else 9)")
        with mock.patch.object(cit, "find_brew", return_value=str(self.stubs / "brew")):
            result, detail = cit.run_route("brew", None, 60)
        self.assertEqual(result, "SKIP")
        self.assertIn("already installed", detail)

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


class ReportTest(unittest.TestCase):
    """A WARN leaves the exit code at 0; under GitHub Actions it's annotated, and every result goes
    to the step summary."""

    def setUp(self):
        d = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, d, True)
        self.summary = d / "summary.md"
        patcher = mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_STEP_SUMMARY": str(self.summary)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, result, detail, route):
        out = io.StringIO()
        with mock.patch.object(cit, "run_route", return_value=(result, detail)), contextlib.redirect_stdout(out):
            code = cit.main(["--path", route])
        return code, out.getvalue()

    def test_slow_brew_warns_and_passes(self):
        code, out = self.run_main("WARN", "98.7 s to first status, over the 90 s limit", "brew")
        self.assertEqual(code, 0, out)
        self.assertIn("WARN brew: 98.7 s to first status, over the 90 s limit\n", out)
        self.assertIn("::warning title=install-time brew::98.7 s to first status, over the 90 s limit\n", out)
        self.assertEqual(self.summary.read_text(), "- WARN brew: 98.7 s to first status, over the 90 s limit\n")

    def test_a_fail_fails_the_run_without_an_annotation(self):
        code, out = self.run_main("FAIL", "200.0 s to first status, over the 180 s ceiling", "brew")
        self.assertEqual(code, 1, out)
        self.assertNotIn("::warning", out)

    def test_a_broken_brew_install_still_fails(self):
        code, out = self.run_main("FAIL", "exit 1 after 40.0 s\nError: no formula", "brew")
        self.assertEqual(code, 1, out)
        self.assertNotIn("::warning", out)
        self.assertEqual(self.summary.read_text(), "- FAIL brew: exit 1 after 40.0 s\n")

    def test_outside_github_actions_there_is_no_annotation_or_summary(self):
        os.environ.pop("GITHUB_ACTIONS")
        code, out = self.run_main("WARN", "95.0 s to first status, over the 90 s limit", "brew")
        self.assertEqual((code, out), (0, "WARN brew: 95.0 s to first status, over the 90 s limit\n"))
        self.assertFalse(self.summary.exists())


class OnPypiTest(unittest.TestCase):
    def answer(self, code, out="", err=""):
        return mock.patch.object(cit.subprocess, "run", return_value=mock.Mock(returncode=code, stdout=out, stderr=err))

    def test_listed_versions_pass_or_skip(self):
        listing = "brainrc (1.2.4)\nAvailable versions: 1.2.4, 1.2.3\n"
        with self.answer(0, listing):
            cit.on_pypi()
            cit.on_pypi("1.2.3")
            with self.assertRaisesRegex(cit.Skip, "brainrc 1.2 is not on PyPI yet"):
                cit.on_pypi("1.2")
        with self.answer(1, err="ERROR: No matching distribution found for brainrc"):
            with self.assertRaisesRegex(cit.Skip, "not on PyPI yet"):
                cit.on_pypi()

    def test_a_pip_that_cannot_answer_is_an_error_not_a_skip(self):
        with self.answer(1, err="No module named pip"):
            with self.assertRaisesRegex(RuntimeError, "couldn't ask PyPI"):
                cit.on_pypi()


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

    def test_the_limit_is_sixty_seconds_and_ninety_for_brew(self):
        self.assertNotIn("--limit", self.text)
        self.assertEqual(cit.LIMITS, {"uvx": 60.0, "pipx": 60.0, "npx": 60.0, "brew": 90.0})
        self.assertEqual(set(cit.LIMITS), set(cit.PATHS))
        self.assertEqual(cit.CEILINGS, {"brew": 180.0})

    def test_main_passes_each_route_its_limit_unless_limit_is_given(self):
        seen = []

        def run(r, local, limit, ceiling):
            seen.append((r, limit, ceiling))
            return "PASS", ""
        with mock.patch.object(cit, "run_route", run), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cit.main(["--path", "uvx", "--path", "brew"]), 0)
            self.assertEqual(cit.main(["--path", "brew", "--limit", "30"]), 0)
        # brew warns from 90 s and fails over 180 s; an explicit --limit is hard, for brew too
        self.assertEqual(seen, [("uvx", 60.0, None), ("brew", 90.0, 180.0), ("brew", 30.0, None)])


if __name__ == "__main__":
    unittest.main()
