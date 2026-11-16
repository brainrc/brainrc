"""scripts/hook_latency.py measures the hooks each tool call fires (#299)."""
import importlib.util
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("hook_latency", REPO / "scripts" / "hook_latency.py")
hook_latency = importlib.util.module_from_spec(spec)
sys.modules["hook_latency"] = hook_latency
spec.loader.exec_module(hook_latency)


class HookLatencyTest(unittest.TestCase):
    def test_percentile_is_nearest_rank(self):
        values = list(range(1, 101))
        self.assertEqual(hook_latency.percentile(values, 95), 95)
        self.assertEqual(hook_latency.percentile(values, 50), 50)
        self.assertEqual(hook_latency.percentile([7.0], 95), 7.0)
        self.assertEqual(hook_latency.percentile([1.0, 2.0], 99.9), 2.0)  # a float pct works

    def test_matchers_follow_claude_code(self):
        self.assertTrue(hook_latency.matches("*", "Bash"))
        self.assertTrue(hook_latency.matches("", "Read"))
        self.assertTrue(hook_latency.matches("Bash|mcp__.*", "mcp__x__y"))
        self.assertFalse(hook_latency.matches("Bash", "BashOutput"))

    def test_each_tool_fires_the_hooks_its_matchers_name(self):
        names = lambda tool: [c.rsplit("/", 1)[1].split('"')[0] for c in hook_latency.hook_commands("PreToolUse", tool)]  # noqa: E731
        self.assertEqual(names("Bash"), ["guard_outward.py", "guard_secrets.py"])
        self.assertEqual(names("Read"), ["guard_secrets.py"])
        self.assertEqual(names("mcp__github__get_issue"), ["guard_outward.py"])
        self.assertEqual(names("WebFetch"), [])
        self.assertEqual(len(hook_latency.hook_commands("SessionStart")), 1)

    def test_a_missing_hook_fails_instead_of_timing_nothing(self):
        with self.assertRaises(SystemExit):
            hook_latency.checked('f="/nonexistent/guard.py"; [ ! -f "$f" ] || python3 "$f"', "{}", {})

    def test_a_short_run_reports_every_case(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(hook_latency.main(["--runs", "1", "--json"]), 0)
        rows = json.loads(out.getvalue())["rows"]
        self.assertEqual(len(rows), len(hook_latency.CALLS) + 5)
        self.assertTrue(all(r["median_ms"] > 0 and r["p95_ms"] >= r["median_ms"] for r in rows))


if __name__ == "__main__":
    unittest.main()
