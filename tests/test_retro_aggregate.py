import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from retro_aggregate import aggregate  # noqa: E402
from retro_metrics import RunRecord  # noqa: E402


def rec(path, **kw):
    kw.setdefault("stage", "done")
    return RunRecord(path=path, **kw)


class AggregateTest(unittest.TestCase):
    def test_counts_by_size_mode_and_stage(self):
        a = aggregate([
            rec("a", size="standard", mode="auto"),
            rec("b", size="standard", mode="guided"),
            rec("c", size="small", mode="auto", stage="implement"),
            rec("d", size="small", mode="auto", stage="plan", blocked_reason="needs input"),
        ])
        self.assertEqual(a["runs"], 4)
        self.assertEqual(a["by_size"]["standard"]["runs"], 2)
        self.assertEqual(a["by_size"]["small"]["runs"], 2)
        self.assertEqual(a["by_mode"]["auto"]["runs"], 3)
        self.assertEqual(a["by_mode"]["guided"]["runs"], 1)
        self.assertEqual(
            {k: v["runs"] for k, v in a["by_stage"].items()},
            {"done": 2, "in progress": 1, "blocked": 1},
        )

    def test_multi_domain_counts_under_each_and_none_group(self):
        a = aggregate([
            rec("a", domains=["scripting", "docs"]),
            rec("b", domains=["scripting"]),
            rec("c", domains=[]),
            rec("d", domains=None),
        ])
        d = {k: v["runs"] for k, v in a["by_domain"].items()}
        self.assertEqual(d, {"scripting": 2, "docs": 1, "none": 2})
        self.assertGreater(sum(d.values()), 0)
        self.assertEqual(a["runs"], 4)
        self.assertIn("sum past", a["domain_note"])

    def test_averages_use_known_values_only_with_n(self):
        a = aggregate([
            rec("a", retries=2, interventions=1),
            rec("b", retries=4),
            rec("c", retries=None, interventions=None),
        ])
        avg = a["overall"]["averages"]
        self.assertEqual(avg["retries"], {"avg": 3.0, "n": 2})
        self.assertEqual(avg["interventions"], {"avg": 1.0, "n": 1})
        self.assertEqual(a["overall"]["runs"], 3)

    def test_unknown_everywhere_gives_none_avg_and_zero_n(self):
        avg = aggregate([rec("a")])["overall"]["averages"]
        self.assertEqual(avg["retries"], {"avg": None, "n": 0})

    def test_zero_is_a_known_value(self):
        avg = aggregate([rec("a", retries=0), rec("b", retries=2)])["overall"]["averages"]
        self.assertEqual(avg["retries"], {"avg": 1.0, "n": 2})

    def test_duration_averages_use_done_runs_only(self):
        a = aggregate([
            rec("a", total_minutes=10.0, wait_minutes=4.0, agent_minutes=6.0),
            rec("b", total_minutes=20.0, wait_minutes=None, agent_minutes=None),
            rec("c", stage="implement", total_minutes=100.0, agent_minutes=100.0),
            rec("d", stage="plan", blocked_reason="x", total_minutes=50.0),
        ])
        avg = a["overall"]["averages"]
        self.assertEqual(avg["total_minutes"], {"avg": 15.0, "n": 2})
        self.assertEqual(avg["agent_minutes"], {"avg": 6.0, "n": 1})
        self.assertEqual(avg["wait_minutes"], {"avg": 4.0, "n": 1})

    def test_non_duration_averages_include_unfinished_runs(self):
        avg = aggregate([
            rec("a", retries=1),
            rec("b", stage="implement", retries=3),
        ])["overall"]["averages"]
        self.assertEqual(avg["retries"], {"avg": 2.0, "n": 2})

    def test_first_pass_and_wave_ratio_averages(self):
        avg = aggregate([
            rec("a", first_pass_rate=1.0, wave_ratio=2.0),
            rec("b", first_pass_rate=0.5),
        ])["overall"]["averages"]
        self.assertEqual(avg["first_pass_rate"], {"avg": 0.75, "n": 2})
        self.assertEqual(avg["wave_ratio"], {"avg": 2.0, "n": 1})

    def test_group_averages_are_per_group(self):
        a = aggregate([
            rec("a", size="small", retries=0),
            rec("b", size="standard", retries=4),
        ])
        self.assertEqual(a["by_size"]["small"]["averages"]["retries"], {"avg": 0.0, "n": 1})
        self.assertEqual(a["by_size"]["standard"]["averages"]["retries"], {"avg": 4.0, "n": 1})

    def test_missing_size_and_mode_grouped_as_unknown(self):
        a = aggregate([rec("a")])
        self.assertEqual(a["by_size"]["unknown"]["runs"], 1)
        self.assertEqual(a["by_mode"]["unknown"]["runs"], 1)

    def test_blocked_stops_current_and_past_with_reasons(self):
        a = aggregate([
            rec("a", size="small", mode="auto", domains=["scripting"], stage="plan",
                blocked_reason="needs input", blocked_stops=["old failure"]),
            rec("b", size="standard", mode="auto", domains=["docs"], blocked_stops=[]),
            rec("c", size="standard", mode="guided", blocked_stops=None),
            rec("d", size="standard", mode="auto", blocked_stops=["old failure"]),
        ])
        bs = a["blocked_stops"]
        self.assertEqual(bs["count"], 3)
        self.assertEqual(sorted(bs["reasons"]), ["needs input", "old failure", "old failure"])
        self.assertEqual(a["by_size"]["small"]["blocked_stops"]["count"], 2)
        self.assertEqual(a["by_size"]["standard"]["blocked_stops"]["count"], 1)
        self.assertEqual(a["by_mode"]["auto"]["blocked_stops"]["count"], 3)
        self.assertEqual(a["by_mode"]["guided"]["blocked_stops"]["count"], 0)
        self.assertEqual(a["by_domain"]["scripting"]["blocked_stops"]["reasons"],
                         ["needs input", "old failure"])
        self.assertEqual(a["by_domain"]["docs"]["blocked_stops"]["count"], 0)
        self.assertEqual(a["by_domain"]["none"]["blocked_stops"]["count"], 1)

    def test_blocked_stop_entries_may_be_dicts_with_reason(self):
        a = aggregate([rec("a", blocked_stops=[{"reason": "r1"}])])
        self.assertEqual(a["blocked_stops"]["reasons"], ["r1"])

    def test_empty_input(self):
        a = aggregate([])
        self.assertEqual(a["runs"], 0)
        self.assertEqual(a["blocked_stops"]["count"], 0)
        self.assertEqual(a["by_size"], {})


if __name__ == "__main__":
    unittest.main()
