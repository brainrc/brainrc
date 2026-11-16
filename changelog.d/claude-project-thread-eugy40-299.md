---
bump: patch
---
- `scripts/hook_latency.py` measures the median and p95 wall time core's hooks add to each tool
  call (Claude Code and Cursor) and to session start, and the `hook-latency` workflow runs it on
  Linux and macOS. `docs/hook-latency.md` records the numbers and the go or no-go note on a native
  rewrite (#299).
