# Retro: 042-disabled-harness-hooks

Ticket: gh:42 · Size: small · PR: https://github.com/bxker/ai-config/pull/43

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / skipped / 0 |
| Tasks | 1 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 5/5 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? The real run caught a leftover `"hooks": {}`
   the unit tests allowed; same lesson as #12 and #17: run user-facing behaviour for real.
4. Process: `rm -rf $HOME` while faking a home dir was blocked by the safety check (it saw
   /root). Fake homes should be fresh directories, never deleted through `$HOME`.
