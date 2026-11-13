"""Tests for scripts/retro_ccusage.py: period totals from `ccusage daily --json`, using a stub
`ccusage` executable on PATH. Never needs the real tool or network."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import retro_ccusage  # noqa: E402
from support import rmtree  # noqa: E402

SINCE, UNTIL = date(2026, 10, 1), date(2026, 10, 20)


class CcusageTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = str(self.bin)  # only the stub dir: real ccusage never found

    def tearDown(self):
        os.environ["PATH"] = self.old_path
        rmtree(self.root)

    def stub(self, body: str):
        path = self.bin / "ccusage"
        path.write_text(f"#!{sys.executable}\n{body}\n")
        path.chmod(0o755)

    def test_missing_is_unavailable(self):
        r = retro_ccusage.period_totals(SINCE, UNTIL)
        self.assertFalse(r["available"])
        self.assertIsNone(r["tokens"])
        self.assertIsNone(r["cost"])
        self.assertIn("unavailable", r["note"].lower())

    def test_non_zero_exit_is_unavailable(self):
        self.stub("import sys\nprint('boom', file=sys.stderr)\nsys.exit(3)")
        r = retro_ccusage.period_totals(SINCE, UNTIL)
        self.assertFalse(r["available"])
        self.assertIsNone(r["tokens"])
        self.assertIn("unavailable", r["note"].lower())

    def test_bad_json_is_unavailable(self):
        self.stub("print('not json')")
        r = retro_ccusage.period_totals(SINCE, UNTIL)
        self.assertFalse(r["available"])
        self.assertIn("unavailable", r["note"].lower())

    def test_missing_keys_is_unavailable(self):
        self.stub("print('{\"other\": 1}')")
        r = retro_ccusage.period_totals(SINCE, UNTIL)
        self.assertFalse(r["available"])

    def test_timeout_is_unavailable(self):
        self.stub("import time\ntime.sleep(5)")
        r = retro_ccusage.period_totals(SINCE, UNTIL, timeout=0.5)
        self.assertFalse(r["available"])
        self.assertIn("unavailable", r["note"].lower())

    def test_success_uses_totals_and_range_flags(self):
        out = {"daily": [], "totals": {"totalTokens": 1500, "totalCost": 2.5}}
        args_file = self.root / "args.json"
        self.stub(
            "import json, sys\n"
            f"json.dump(sys.argv[1:], open({str(args_file)!r}, 'w'))\n"
            f"print({json.dumps(json.dumps(out))})"
        )
        r = retro_ccusage.period_totals(SINCE, UNTIL)
        self.assertTrue(r["available"])
        self.assertEqual(r["tokens"], 1500)
        self.assertEqual(r["cost"], 2.5)
        self.assertEqual(r["since"], "2026-10-01")
        self.assertEqual(r["until"], "2026-10-20")
        args = json.loads(args_file.read_text())
        self.assertEqual(args[:2], ["daily", "--json"])
        self.assertEqual(args[args.index("--since") + 1], "20261001")
        self.assertEqual(args[args.index("--until") + 1], "20261020")

    def test_success_sums_daily_when_no_totals(self):
        out = {"daily": [{"totalTokens": 100, "totalCost": 0.5},
                         {"totalTokens": 200, "totalCost": 0.25}]}
        self.stub(f"print({json.dumps(json.dumps(out))})")
        r = retro_ccusage.period_totals(SINCE, UNTIL)
        self.assertTrue(r["available"])
        self.assertEqual(r["tokens"], 300)
        self.assertEqual(r["cost"], 0.75)


if __name__ == "__main__":
    unittest.main()
