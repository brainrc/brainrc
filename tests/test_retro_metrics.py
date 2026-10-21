"""Tests for scripts/retro_metrics.py: load one spec-agent run folder into a RunRecord (or Skipped)
with per-run metrics. Unknown is None, never 0; invalid timestamps warn and are never clamped."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from retro_metrics import RunRecord, Skipped, load_run  # noqa: E402

COMPLETE = {
    "version": 1,
    "slug": "001-demo",
    "size": "standard",
    "mode": "subagent",
    "stage": "done",
    "domains": ["scripting", "docs"],
    "blocked": None,
    "gates": {"spec": "approved", "plan": "approved", "deliver": "approved"},
    "metrics": {
        "started_at": "2026-10-01T10:00:00Z",
        "stage_started_at": {
            "intake": "2026-10-01T10:00:00Z",
            "spec": "2026-10-01T10:10:00Z",
            "plan": "2026-10-01T10:40:00Z",
            "implement": "2026-10-01T11:00:00Z",
            "verify": "2026-10-01T12:00:00Z",
            "document": "2026-10-01T12:10:00Z",
            "deliver": "2026-10-01T12:20:00Z",
            "done": "2026-10-01T12:50:00Z",
        },
        "gates": {
            "spec": {"presented_at": "2026-10-01T10:30:00Z", "approved_at": "2026-10-01T10:40:00Z"},
            "plan": {"presented_at": "2026-10-01T10:50:00Z", "approved_at": "2026-10-01T11:00:00Z"},
            "deliver": {"presented_at": "2026-10-01T12:20:00Z", "approved_at": "2026-10-01T12:50:00Z"},
        },
        "gate_rework": {"spec": 0, "plan": 1, "deliver": 0},
        "reviews": {"total": 4, "first_pass": 3},
        "retries": 2,
        "interventions": 1,
        "waves": {"count": 2, "max_width": 3, "task_minutes": 60, "wall_minutes": 30},
    },
}


class RetroMetricsTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, state, slug="001-demo", raw=None) -> Path:
        run = self.root / "specs" / slug
        run.mkdir(parents=True, exist_ok=True)
        (run / "state.json").write_text(raw if raw is not None else json.dumps(state))
        return run

    def load(self, state) -> RunRecord:
        rec = load_run(self.write(state))
        self.assertIsInstance(rec, RunRecord, rec)
        return rec

    # AC4
    def test_complete_run_durations(self):
        rec = self.load(COMPLETE)
        self.assertEqual(rec.total_minutes, 170)
        self.assertEqual(rec.wait_minutes, 50)
        self.assertEqual(rec.agent_minutes, 120)
        self.assertEqual(rec.warnings, [])

    def test_per_stage_excludes_gate_wait(self):
        rec = self.load(COMPLETE)
        self.assertEqual(
            rec.stage_minutes,
            {"intake": 10, "spec": 30 - 10, "plan": 20 - 10, "implement": 60,
             "verify": 10, "document": 10, "deliver": 0},
        )

    # AC5
    def test_rework_first_pass_retries_interventions(self):
        rec = self.load(COMPLETE)
        self.assertEqual(rec.gate_rework, {"spec": 0, "plan": 1, "deliver": 0})
        self.assertEqual(rec.first_pass_rate, 0.75)
        self.assertEqual(rec.retries, 2)
        self.assertEqual(rec.interventions, 1)

    def test_wave_stats(self):
        rec = self.load(COMPLETE)
        self.assertEqual(rec.waves["task_minutes"], 60)
        self.assertEqual(rec.waves["wall_minutes"], 30)
        self.assertEqual(rec.wave_ratio, 2.0)

    def test_identity_fields(self):
        rec = self.load(COMPLETE)
        self.assertEqual((rec.slug, rec.size, rec.mode, rec.stage), ("001-demo", "standard", "subagent", "done"))
        self.assertEqual(rec.domains, ["scripting", "docs"])
        self.assertIsNone(rec.blocked_reason)
        self.assertIsNone(rec.criteria_passed)
        self.assertEqual(rec.blocked_stops, [])

    def test_path_label(self):
        run = self.write(COMPLETE)
        rec = load_run(run, label="specs/001-demo")
        self.assertEqual(rec.path, "specs/001-demo")

    # AC6
    def test_old_format_unknowns_are_none(self):
        old = {"slug": "002-old", "stage": "done",
               "metrics": {"started_at": "2026-10-01T10:00:00Z",
                           "stage_started_at": {"intake": "2026-10-01T10:00:00Z",
                                                "done": "2026-10-01T11:00:00Z"}}}
        rec = self.load(old)
        self.assertEqual(rec.total_minutes, 60)
        self.assertIsNone(rec.wait_minutes)
        self.assertIsNone(rec.agent_minutes)
        self.assertIsNone(rec.stage_minutes)
        self.assertIsNone(rec.gate_rework)
        self.assertIsNone(rec.first_pass_rate)
        self.assertIsNone(rec.retries)
        self.assertIsNone(rec.interventions)
        self.assertIsNone(rec.waves)
        self.assertIsNone(rec.wave_ratio)
        self.assertIsNone(rec.domains)
        self.assertIsNone(rec.size)
        self.assertIsNone(rec.mode)
        self.assertEqual(rec.warnings, [])

    def test_no_metrics_at_all(self):
        rec = self.load({"slug": "003", "stage": "done"})
        self.assertIsNone(rec.total_minutes)
        self.assertIsNone(rec.retries)

    def test_zero_values_stay_zero(self):
        st = copy.deepcopy(COMPLETE)
        st["metrics"]["retries"] = 0
        st["metrics"]["interventions"] = 0
        st["metrics"]["reviews"] = {"total": 2, "first_pass": 0}
        rec = self.load(st)
        self.assertEqual(rec.retries, 0)
        self.assertEqual(rec.interventions, 0)
        self.assertEqual(rec.first_pass_rate, 0.0)

    def test_zero_reviews_rate_unknown(self):
        st = copy.deepcopy(COMPLETE)
        st["metrics"]["reviews"] = {"total": 0, "first_pass": 0}
        self.assertIsNone(self.load(st).first_pass_rate)

    def test_wrong_types_are_unknown(self):
        st = copy.deepcopy(COMPLETE)
        st["metrics"]["retries"] = "many"
        st["metrics"]["interventions"] = True
        st["domains"] = "scripting"
        rec = self.load(st)
        self.assertIsNone(rec.retries)
        self.assertIsNone(rec.interventions)
        self.assertIsNone(rec.domains)

    # AC7
    def test_skipped_cases(self):
        cases = {
            "invalid json": "{not json",
            "not object": "[1, 2]",
            "empty": "",
        }
        for name, raw in cases.items():
            with self.subTest(name):
                res = load_run(self.write(None, slug="bad-" + name.replace(" ", "-"), raw=raw))
                self.assertIsInstance(res, Skipped)
                self.assertTrue(res.reason)

    def test_unreadable_missing_and_non_utf8(self):
        missing = self.root / "specs" / "nope"
        missing.mkdir(parents=True)
        res = load_run(missing)
        self.assertIsInstance(res, Skipped)
        self.assertTrue(res.reason)
        run = self.root / "specs" / "bin"
        run.mkdir()
        (run / "state.json").write_bytes(b"\xff\xfe\x00")
        self.assertIsInstance(load_run(run), Skipped)

    def test_skipped_label(self):
        run = self.write(None, raw="[]")
        self.assertEqual(load_run(run, label="specs/001-demo").path, "specs/001-demo")

    # AC8
    def test_in_progress_run(self):
        st = copy.deepcopy(COMPLETE)
        st["stage"] = "implement"
        del st["metrics"]["stage_started_at"]["verify"]
        del st["metrics"]["stage_started_at"]["document"]
        del st["metrics"]["stage_started_at"]["deliver"]
        del st["metrics"]["stage_started_at"]["done"]
        del st["metrics"]["gates"]["deliver"]
        st["metrics"].pop("waves")
        rec = self.load(st)
        self.assertEqual(rec.stage, "implement")
        self.assertIsNone(rec.total_minutes)
        self.assertIsNone(rec.wait_minutes)
        self.assertIsNone(rec.agent_minutes)
        self.assertIsNone(rec.stage_minutes)
        self.assertIsNone(rec.waves)
        self.assertEqual(rec.warnings, [])

    def test_blocked_run(self):
        st = copy.deepcopy(COMPLETE)
        st["stage"] = "implement"
        st["blocked"] = {"reason": "needs creds", "stage": "implement", "task": "T2", "since": "x"}
        rec = self.load(st)
        self.assertEqual(rec.blocked_reason, "needs creds")
        self.assertIsNone(rec.total_minutes)

    def test_blocked_without_reason_text(self):
        st = {"slug": "x", "stage": "plan", "blocked": {"stage": "plan"}}
        rec = self.load(st)
        self.assertIsNotNone(rec.blocked_reason)
        self.assertEqual(rec.blocked_reason, "unknown")

    # AC18
    def test_approved_before_presented(self):
        st = copy.deepcopy(COMPLETE)
        g = st["metrics"]["gates"]["plan"]
        g["presented_at"], g["approved_at"] = g["approved_at"], g["presented_at"]
        rec = self.load(st)
        self.assertTrue(any("plan" in w and "approved_at" in w for w in rec.warnings), rec.warnings)
        self.assertIsNone(rec.wait_minutes)
        self.assertIsNone(rec.agent_minutes)
        self.assertEqual(rec.total_minutes, 170)  # not adjusted
        self.assertIsNone(rec.stage_minutes["plan"])

    def test_out_of_order_stages(self):
        st = copy.deepcopy(COMPLETE)
        st["metrics"]["stage_started_at"]["implement"] = "2026-10-01T10:20:00Z"
        rec = self.load(st)
        self.assertTrue(any("out of order" in w for w in rec.warnings), rec.warnings)
        self.assertIsNone(rec.stage_minutes["plan"])
        self.assertIsNone(rec.stage_minutes["implement"])
        self.assertEqual(rec.stage_minutes["intake"], 10)

    def test_negative_total(self):
        st = copy.deepcopy(COMPLETE)
        st["metrics"]["stage_started_at"]["done"] = "2026-10-01T09:00:00Z"
        rec = self.load(st)
        self.assertTrue(any("negative" in w for w in rec.warnings), rec.warnings)
        self.assertIsNone(rec.total_minutes)
        self.assertIsNone(rec.agent_minutes)

    def test_unparseable_timestamp(self):
        st = copy.deepcopy(COMPLETE)
        st["metrics"]["started_at"] = "yesterday"
        rec = self.load(st)
        self.assertTrue(any("started_at" in w for w in rec.warnings), rec.warnings)
        self.assertIsNone(rec.total_minutes)

    def test_aicfg_doctor_shape_does_not_crash(self):
        st = copy.deepcopy(COMPLETE)
        ts = st["metrics"]["stage_started_at"]
        ts["plan"], ts["implement"] = "2026-10-01T11:59:56Z", "2026-10-01T05:05:00Z"
        g = st["metrics"]["gates"]["plan"]
        g["presented_at"], g["approved_at"] = "2026-10-01T11:59:56Z", "2026-10-01T05:05:00Z"
        rec = self.load(st)
        self.assertTrue(rec.warnings)
        self.assertIsNone(rec.wait_minutes)
        self.assertIsNone(rec.agent_minutes)
        for v in (rec.stage_minutes or {}).values():
            self.assertTrue(v is None or v >= 0)

    # AC17
    def run_with(self, verify=None, retro=None, log=None, state=COMPLETE) -> RunRecord:
        run = self.write(state)
        for name, text in (("verify.md", verify), ("retro.md", retro), ("log.md", log)):
            if text is not None:
                (run / name).write_text(text)
        rec = load_run(run)
        self.assertIsInstance(rec, RunRecord, rec)
        return rec

    VERIFY = ("# Verify: x\n\n## Checks\n| Check | Command | Result |\n|---|---|---|\n"
              "| Tests | `t` | pass |\n\n## Acceptance criteria\n"
              "| Criterion | Evidence | Result |\n|---|---|---|\n"
              "| AC1 | e | pass |\n| AC2 | e | fail |\n| AC3 | e | pass |\n\n## Notes\n")
    RETRO = "## Metrics\n| Metric | Value |\n|---|---|\n| Criteria passed | 5/6 |\n"

    def test_criteria_from_verify_table(self):
        self.assertEqual(self.run_with(verify=self.VERIFY).criteria_passed, "2/3")

    def test_criteria_result_column_found_by_header(self):
        v = ("## Acceptance criteria\n| Criterion | Result | Evidence |\n|---|---|---|\n"
             "| AC1 | pass | fail mentioned here |\n| AC2 | fail | pass in evidence |\n")
        self.assertEqual(self.run_with(verify=v).criteria_passed, "1/2")

    def test_criteria_verify_wins_over_retro(self):
        self.assertEqual(self.run_with(verify=self.VERIFY, retro=self.RETRO).criteria_passed, "2/3")

    def test_criteria_retro_fallback(self):
        self.assertEqual(self.run_with(retro=self.RETRO).criteria_passed, "5/6")
        no_table = "# Verify: x\n\n## Checks\n| Check | Result |\n|---|---|\n| T | pass |\n"
        self.assertEqual(self.run_with(verify=no_table, retro=self.RETRO).criteria_passed, "5/6")

    def test_criteria_without_result_header_is_unknown(self):
        v = "## Acceptance criteria\n| Criterion | Evidence | Outcome |\n|---|---|---|\n| AC1 | e | pass |\n"
        self.assertIsNone(self.run_with(verify=v).criteria_passed)

    def test_criteria_unknown(self):
        self.assertIsNone(self.run_with().criteria_passed)
        placeholder = "| Criteria passed | <n>/<n> |\n"
        self.assertIsNone(self.run_with(retro=placeholder).criteria_passed)

    # AC9
    LOG = ("## implementer \u00b7 T1 \u00b7 done\n2026-10-01T10:00:00Z\n\n**Open issues:** none\n\n"
           "## implementer \u00b7 T2 \u00b7 blocked\n2026-10-01T10:05:00Z\n\n"
           "**Did:** x\n\n**Open issues:** needs creds\n\n**Next:** ask\n\n"
           "## reviewer \u00b7 T2 \u00b7 blocked\n2026-10-01T10:09:00Z\n\n**Did:** y\n\n"
           "## reviewer \u00b7 T3 \u00b7 changes-requested\n2026-10-01T10:10:00Z\n")

    def test_blocked_stops_from_log(self):
        rec = self.run_with(log=self.LOG)
        self.assertEqual(rec.blocked_stops, ["needs creds", "unknown"])

    def test_blocked_stops_current_plus_past(self):
        st = copy.deepcopy(COMPLETE)
        st["blocked"] = {"reason": "waiting", "stage": "implement"}
        rec = self.run_with(log=self.LOG, state=st)
        self.assertEqual(rec.blocked_stops, ["waiting", "needs creds", "unknown"])

    def test_blocked_stops_no_log_only_current(self):
        st = copy.deepcopy(COMPLETE)
        st["blocked"] = {"reason": "waiting"}
        self.assertEqual(self.run_with(state=st).blocked_stops, ["waiting"])

    def test_blocked_word_outside_header_not_counted(self):
        log = "## implementer \u00b7 T1 \u00b7 done\n\n**Did:** was blocked \u00b7 but fixed\n"
        self.assertEqual(self.run_with(log=log).blocked_stops, [])


if __name__ == "__main__":
    unittest.main()
