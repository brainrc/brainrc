Shipped `scripts/retro_report.py`: an offline rollup of `specs/*/state.json` across one or more `--root` dirs, as Markdown or `--json` (schema v1). Optional `--ccusage` adds period-total tokens and cost. Documented in `docs/efficiency.md#metrics-rollup`.
Verify: `python3 -m unittest discover -s tests` (306 pass, offline), then `python3 scripts/retro_report.py --root specs`.
Not yet checked against a real ccusage install: its flags and JSON shape are stub-tested only.
PR: <PR_URL>
