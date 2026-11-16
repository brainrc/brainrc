"""A pack's own tests (#138): pack.toml `test` names them, `validate --pack` runs them, and
brainrc.testing runs a guard hook for them."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet  # noqa: E402
from brainrc import testing  # noqa: E402
from brainrc.testing import (assert_allows, assert_asks, assert_denies, assert_no_opinion,  # noqa: E402
                             bash, run_hook)
from support import rmtree  # noqa: E402

HOOK = "overrides/claude/hooks/guard_homelab.py"


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class HelpersTest(unittest.TestCase):
    """Each decision a hook can make, from a stand-in hook that echoes what the payload asks for."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(rmtree, self.dir)
        self.hook = write(self.dir / "hook.py", """import json, sys
cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
if cmd == "block":
    sys.exit(2)
if cmd == "crash":
    sys.exit("boom")
if cmd == "hang":
    import time; time.sleep(30)
if cmd == "noise":
    print("not a decision")
elif cmd == "context":
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "x"}}))
elif cmd in ("allow", "ask", "deny", "maybe"):
    print(json.dumps({"hookSpecificOutput": {"permissionDecision": cmd}}))
""")

    def test_run_hook_reads_each_decision(self):
        for cmd, want in [("allow", "allow"), ("ask", "ask"), ("deny", "deny"), ("block", "deny"), ("ls", None),
                          ("context", None)]:
            with self.subTest(cmd=cmd):
                self.assertEqual(run_hook(self.hook, bash(cmd)), want)

    def test_a_hook_that_fails_or_prints_nonsense_is_an_assertion_error(self):
        for cmd, why in [("crash", "exited 1: boom"), ("noise", "isn't hook JSON"), ("maybe", "decided 'maybe'")]:
            with self.subTest(cmd=cmd), self.assertRaises(AssertionError) as raised:
                run_hook(self.hook, bash(cmd))
            self.assertIn(why, str(raised.exception))

    def test_the_asserts(self):
        assert_denies(self.hook, "deny", "block")
        assert_asks(self.hook, "ask")
        assert_allows(self.hook, "allow", "ls", {"tool_name": "Read", "tool_input": {}})

    def test_a_failed_assert_lists_every_wrong_case(self):
        with self.assertRaises(AssertionError) as raised:
            assert_asks(self.hook, "ask", "ls", "deny")
        self.assertEqual(str(raised.exception),
                         "hook.py should ask, but:\n  'ls': no opinion\n  'deny': deny")
        with self.assertRaises(AssertionError) as raised:
            assert_allows(self.hook, "ask")
        self.assertIn("'ask': ask", str(raised.exception))

    def test_a_missing_hook_fails_rather_than_counting_as_a_deny(self):
        with self.assertRaisesRegex(AssertionError, "no hook at"):
            assert_denies(self.dir / "gone.py", "rm -rf /")

    def test_a_hung_hook_fails_naming_the_wait(self):
        with self.assertRaises(AssertionError) as raised:
            run_hook(self.hook, bash("hang"), timeout=0.5)
        self.assertIn("took over 0.5s", str(raised.exception))

    def test_no_opinion_is_stricter_than_allows(self):
        assert_no_opinion(self.hook, "ls", "context")
        with self.assertRaisesRegex(AssertionError, "'allow': allow"):
            assert_no_opinion(self.hook, "ls", "allow")

    def test_no_cases_is_a_mistake(self):
        with self.assertRaisesRegex(AssertionError, "no commands to check"):
            assert_denies(self.hook)

    def test_a_string_payload_goes_in_as_is(self):
        self.assertEqual(testing.bash("x"), {"tool_name": "Bash", "tool_input": {"command": "x"}})
        with self.assertRaisesRegex(AssertionError, "exited 1"):
            run_hook(self.hook, "not json")


class ValidateRunsPackTestsTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.pack = Path(tempfile.mkdtemp()).resolve() / "homelab"
        self.addCleanup(rmtree, self.pack.parent)
        shutil.copytree(ROOT / "examples/pack-homelab", self.pack)
        self.toml = self.pack / "pack.toml"

    def validate(self):
        return quiet(brainrc.cmd_validate, str(self.pack))

    def test_the_example_packs_tests_pass_and_leave_no_bytecode(self):
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertEqual(list(self.pack.rglob("__pycache__")), [])

    def test_a_rule_that_stops_asking_fails_validate(self):
        guard = self.pack / HOOK
        guard.write_text(guard.read_text().replace("|rollback|migrate)", "|rollback)"))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR homelab:tests: the pack's tests failed:", out)
        self.assertIn("'qm migrate 105 node2': no opinion", out)

    def test_doctor_does_not_run_them(self):
        guard = self.pack / HOOK
        guard.write_text(guard.read_text().replace("|rollback|migrate)", "|rollback)"))
        code, out = quiet(brainrc.cmd_validate, str(self.pack), "homelab")
        self.assertEqual(code, 0, out)

    def test_the_report_stays_in_view_when_a_test_prints(self):
        test = self.pack / "tests/test_guard.py"
        test.write_text(test.read_text().replace("    def test_asks_before_changing_a_guest(self):\n",
                                                 "    def test_asks_before_changing_a_guest(self):\n"
                                                 "        print('\\n'.join(f'debug {i}' for i in range(40)))\n"
                                                 "        self.fail('the rule is gone')\n", 1))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("the rule is gone", out)
        self.assertIn("FAILED (failures=1)", out)

    def test_a_file_unittest_cannot_import_is_named(self):
        shutil.copy(self.pack / "tests/test_guard.py", self.pack / "tests/guard-tests.py")
        self.edit('test = "tests"', 'test = "tests/guard-tests.py"')
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("unittest can't import guard-tests.py", out)

    def test_a_single_file_runs_too(self):
        self.edit('test = "tests"', 'test = "tests/test_guard.py"')
        code, out = self.validate()
        self.assertEqual(code, 0, out)

    def test_a_path_that_is_not_a_test_in_the_pack_fails(self):
        for value in ("missing", "../homelab/pack.toml", "README.md"):
            with self.subTest(value=value):
                self.toml.write_text(self.toml.read_text().replace(self.current(), f'test = "{value}"'))
                code, out = self.validate()
                self.assertEqual(code, 1, out)
                self.assertIn(f"homelab:pack.toml: `test` must name a directory or a .py file in the pack ({value})", out)

    def test_a_directory_with_no_tests_fails(self):
        (self.pack / "empty").mkdir()
        self.edit('test = "tests"', 'test = "empty"')
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("homelab:pack.toml: `test`: empty has no tests", out)

    def test_it_must_be_a_string(self):
        self.edit('test = "tests"', "test = true")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("homelab:pack.toml: test: must be a string", out)

    def current(self) -> str:
        return next(line.split("#")[0].strip() for line in self.toml.read_text().splitlines()
                    if line.startswith("test ="))

    def edit(self, old: str, new: str) -> None:
        text = self.toml.read_text()
        self.assertIn(old, text)
        self.toml.write_text(text.replace(old, new, 1))


if __name__ == "__main__":
    unittest.main()
