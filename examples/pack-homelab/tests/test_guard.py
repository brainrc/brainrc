"""The homelab guard asks before each risky command, and stays out of a safe near-miss (no
opinion, so Claude Code's own permission check still decides).
`validate --pack` runs these (pack.toml: `test = "tests"`)."""
import unittest
from pathlib import Path

from brainrc.testing import assert_asks, assert_no_opinion, run_hook

HOOK = Path(__file__).resolve().parent.parent / "overrides/claude/hooks/guard_homelab.py"


class ProxmoxTest(unittest.TestCase):
    def test_asks_before_changing_a_guest(self):
        assert_asks(HOOK, "qm destroy 105", "pct stop 200", "qm migrate 105 node2",
                    "pct rollback 200 snap1", "sh -c 'qm destroy 105'", "ls;pct shutdown 200")

    def test_allows_reading_one(self):
        assert_no_opinion(HOOK, "qm list", "pct list", "echo qm-destroy", "git status")


class TalosTest(unittest.TestCase):
    def test_asks_before_changing_a_node(self):
        assert_asks(HOOK, "talosctl -n 10.0.0.2 upgrade --image x", "talosctl reset -n 10.0.0.2")

    def test_allows_reading_one(self):
        assert_no_opinion(HOOK, "talosctl -n 10.0.0.2 dashboard", "talosctl -n 10.0.0.2 get members")

    def test_a_verb_after_the_command_ends_is_not_talos(self):
        assert_no_opinion(HOOK, "talosctl -n 10.0.0.2 get members; echo upgrade")


class PayloadTest(unittest.TestCase):
    def test_other_tools_and_bad_payloads_get_no_opinion(self):
        assert_no_opinion(HOOK, {"tool_name": "Read", "tool_input": {"command": "qm destroy 105"}},
                      {"tool_name": "Bash"})
        self.assertIsNone(run_hook(HOOK, "not json"))


if __name__ == "__main__":
    unittest.main()
