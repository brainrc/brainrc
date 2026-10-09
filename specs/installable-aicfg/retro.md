# Retro: installable-aicfg

Ticket: gh:50 · Size: standard · PR: https://github.com/bxker/ai-config/pull/58

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 |
| Retries | 2 (roles counted twice; relative pack paths) |
| Interventions | 0 |
| Criteria passed | 6/6 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? Comparing the real install's output with a
   checkout's found the double-counted roles; writing the user-facing doc found the pack path.
   Do both before the plan is final next time.

## Notes
- hatchling's `exclude` doesn't apply to `force-include`; the code skips the copied roles instead.
- Follow-up: fix hints still print `python3 scripts/aicfg.py`; show `aicfg` when installed.
