# Retro: 050-opencode

Ticket: gh:50 (step 4) + gh:19 · Size: standard · PR: https://github.com/bxker/ai-config/pull/55

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 5/5 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? Installing the real tool first found the hard
   failure (config invalid) and checked the fix (`agent list` with effective denies).

## Notes
- The T1 tests depended on `harnesses.toml` enabling the format, so T2 and T3 went green together.
- #19's E2E sandbox run still needs a model provider login.
