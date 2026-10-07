# Retro: 017-troubleshooting

Ticket: gh:17 · Size: small · PR: https://github.com/bxker/ai-config/pull/41

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / skipped / 0 |
| Tasks | 1 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 4/4 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? Docs that describe behaviour should be
   checked by running it: doing so found a real bug (#42) and two wrong claims in the draft.
4. Delivery pushed once; the done checkpoint waited for the first CI run (fix for the
   gitleaks race seen on #40).
