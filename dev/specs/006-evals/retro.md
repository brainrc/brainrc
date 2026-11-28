# Retro: 006-evals

Ticket: gh:6 · Size: standard · PR: https://github.com/bxker/ai-config/pull/38

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:15 total = ~0:04 agent + 0:10 waiting at gates |
| Time per stage | spec ~1m, plan ~1m, implement ~2m, verify <1m (agent time, gate waits excluded) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 4 |
| Review first-pass rate | 3/3 (100%) |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 7/7 (sandbox cases unproven on a real run until #18) |

## Reflections
1. Did the result match what you meant? Not asked yet.
2. Where did you have to step in, and why? None.
3. One change that would have prevented that? n/a

## Proposed improvements
- One test failed for a setup reason (grading with `main` checked out). Real runs end on the
  feature branch, so `check` could fall back to reading the run folder from `state.branch` via
  `git show` when it isn't in the working tree. Consider after #18 shows whether it matters.
