---
bump: patch
---
- `scripts/hook_latency.py` measures the median and p95 wall time core's hooks add to each tool
  call (Claude Code and Cursor) and to session start, and the `hook-latency` workflow runs it on
  Linux and macOS. `docs/hook-latency.md` records the numbers against the 50 ms p95 bar: under on
  Linux, over on macOS runners, so the outcome is to port only the guard evaluator to Go (#299).
