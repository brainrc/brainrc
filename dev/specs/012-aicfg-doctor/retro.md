# Retro: 012-aicfg-doctor

Ticket: gh:12 · Size: standard · PR: https://github.com/bxker/ai-config/pull/40

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 3 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 9/9 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? Running the feature for real before Verify
   caught a usability problem (37 identical lines) that the unit tests didn't; spec-agent's
   verifier could require one real run for user-facing commands.
4. Process slip: one red check stashed the whole file and produced an error, not an assertion
   failure; redone by disabling only the new branch. Red checks should toggle the one change.
