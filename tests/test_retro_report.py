"""Tests for scripts/retro_report.py (CLI), run as a subprocess against fixture run folders in temp
dirs. ccusage is a stub on PATH (or absent). Never needs network or the real tool."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "retro_report.py"

COMPLETE = {
    "slug": "001-done", "size": "standard", "mode": "supervised", "domains": ["scripting", "docs"],
    "stage": "done", "blocked": None,
    "metrics": {
        "started_at": "2026-10-01T10:00:00+00:00",
        "stage_started_at": {"intake": "2026-10-01T10:00:00+00:00", "spec": "2026-10-01T10:10:00+00:00",
                             "done": "2026-10-02T10:00:00+00:00"},
        "gates": {"spec": {"presented_at": "2026-10-01T10:20:00+00:00",
                           "approved_at": "2026-10-01T10:40:00+00:00"}},
        "reviews": {"total": 4, "first_pass": 3}, "retries": 1, "interventions": 2,
    },
}
OLD = {"slug": "002-old", "size": "small", "stage": "done"}
INPROG = {"slug": "003-wip", "size": "standard", "mode": "auto", "stage": "implement"}
BLOCKED = {"slug": "004-blocked", "size": "small", "mode": "auto", "stage": "plan",
           "blocked": {"reason": "needs decision"}}


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.calls = self.tmp / "calls.txt"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_dir(self, root: Path, slug: str, state, raw: str | None = None) -> Path:
        d = root / "specs" / slug
        d.mkdir(parents=True)
        (d / "state.json").write_text(raw if raw is not None else json.dumps(state))
        return d

    def fixtures(self, root: Path):
        self.run_dir(root, "001-done", COMPLETE)
        self.run_dir(root, "002-old", OLD)
        self.run_dir(root, "003-wip", INPROG)
        d = self.run_dir(root, "004-blocked", BLOCKED)
        (d / "log.md").write_text("## implementer · T1 · blocked\n**Open issues:** earlier snag\n")
        self.run_dir(root, "005-bad", None, raw="{not json")

    def stub(self, body: str):
        p = self.bin / "ccusage"
        p.write_text(f"#!{sys.executable}\n{body}\n")
        p.chmod(0o755)

    def cli(self, *args, cwd=None, path=None):
        env = {**os.environ, "PATH": path if path is not None else str(self.bin)}
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                              cwd=cwd or self.tmp, env=env, timeout=60)

    def test_help_lists_flags(self):
        r = self.cli("--help")
        self.assertEqual(r.returncode, 0)
        for flag in ("--root", "--json", "--ccusage"):
            self.assertIn(flag, r.stdout)

    def test_default_root_is_cwd_specs(self):
        self.fixtures(self.tmp / "proj")
        r = self.cli("--json", cwd=self.tmp / "proj")
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = json.loads(r.stdout)
        self.assertEqual(len(doc["runs"]), 4)

    def test_multiple_roots_and_dedupe(self):
        a, b = self.tmp / "a", self.tmp / "b"
        self.run_dir(a, "001-done", COMPLETE)
        self.run_dir(b, "009-other", OLD)
        r = self.cli("--json", "--root", str(a), "--root", str(b), "--root", str(a / "."))
        doc = json.loads(r.stdout)
        self.assertEqual(sorted(x["slug"] for x in doc["runs"]), ["001-done", "002-old"])
        paths = [x["path"] for x in doc["runs"]]
        self.assertTrue(any(p.startswith(str(a)) for p in paths))
        self.assertTrue(any(p.startswith(str(b)) for p in paths))

    def test_root_may_be_specs_dir_itself(self):
        self.fixtures(self.tmp / "proj")
        r = self.cli("--json", "--root", "specs", cwd=self.tmp / "proj")
        self.assertEqual(len(json.loads(r.stdout)["runs"]), 4)

    def test_json_document_shape(self):
        self.fixtures(self.tmp)
        r = self.cli("--json", "--root", ".")
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = json.loads(r.stdout)
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(len(doc["runs"]), 4)
        self.assertEqual(len(doc["skipped"]), 1)
        self.assertIn("invalid JSON", doc["skipped"][0]["reason"])
        self.assertIn("by_size", doc["aggregates"])
        runs = {x["slug"]: x for x in doc["runs"]}
        self.assertEqual(runs["001-done"]["total_minutes"], 1440)
        self.assertEqual(runs["001-done"]["wait_minutes"], 20)
        self.assertIsNone(runs["002-old"]["total_minutes"])
        self.assertIsNone(runs["002-old"]["retries"])
        self.assertEqual(runs["004-blocked"]["blocked_reason"], "needs decision")
        self.assertIn("count", doc["aggregates"]["blocked_stops"])
        self.assertIn("usage", doc)

    def test_markdown_default(self):
        self.fixtures(self.tmp)
        r = self.cli("--root", ".")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("| Run", out)
        self.assertIn("001-done", out)
        self.assertIn("unknown", out)
        self.assertIn("n/a", out)
        self.assertIn("needs decision", out)
        self.assertIn("earlier snag", out)
        self.assertIn("005-bad", out)  # skipped list
        self.assertIn("domain rows can sum past the run count", out)
        self.assertIn("by size", out.lower())
        with self.assertRaises(ValueError):
            json.loads(out)

    def test_no_ccusage_flag_never_invokes_it(self):
        self.fixtures(self.tmp)
        self.stub(f"open({str(self.calls)!r}, 'a').write('called')\nprint('{{}}')")
        for extra in ((), ("--json",)):
            r = self.cli("--root", ".", *extra)
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.calls.exists())
        doc = json.loads(self.cli("--root", ".", "--json").stdout)
        self.assertIsNone(doc["usage"]["tokens"])
        self.assertIsNone(doc["usage"]["cost"])

    def test_ccusage_missing_degrades(self):
        self.fixtures(self.tmp)
        r = self.cli("--root", ".", "--ccusage")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("n/a", r.stdout)
        self.assertIn("unavailable", r.stdout.lower())
        doc = json.loads(self.cli("--root", ".", "--json", "--ccusage").stdout)
        self.assertIsNone(doc["usage"]["tokens"])
        self.assertIsNone(doc["usage"]["cost"])
        self.assertIn("unavailable", doc["usage"]["note"])

    def test_ccusage_failing_degrades(self):
        self.fixtures(self.tmp)
        self.stub("import sys\nsys.exit(2)")
        r = self.cli("--root", ".", "--ccusage")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("unavailable", r.stdout.lower())

    def test_ccusage_period_total(self):
        self.fixtures(self.tmp)
        out = {"totals": {"totalTokens": 1234, "totalCost": 5.5}}
        self.stub("import json, sys\n"
                  f"open({str(self.calls)!r}, 'w').write(' '.join(sys.argv[1:]))\n"
                  f"print({json.dumps(json.dumps(out))})")
        r = self.cli("--root", ".", "--ccusage")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1234", r.stdout)
        self.assertIn("5.5", r.stdout)
        self.assertIn("period total", r.stdout.lower())
        args = self.calls.read_text()
        self.assertIn("--since 20261001", args)
        self.assertIn("--until 20261002", args)
        doc = json.loads(self.cli("--root", ".", "--json", "--ccusage").stdout)
        self.assertEqual(doc["usage"]["tokens"], 1234)
        self.assertEqual(doc["usage"]["cost"], 5.5)
        self.assertEqual(doc["usage"]["since"], "2026-10-01")

    def test_output_has_no_absolute_paths_beyond_root(self):
        self.fixtures(self.tmp)
        for extra in ((), ("--json",)):
            r = self.cli("--root", ".", *extra)
            self.assertNotIn(str(self.tmp), r.stdout)


if __name__ == "__main__":
    unittest.main()
