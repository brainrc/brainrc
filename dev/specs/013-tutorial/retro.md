# Retro: 013-tutorial

Ticket: gh:13 · Size: standard · PR: https://github.com/bxker/ai-config/pull/36

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 4:58 total = ~0:02 agent + 4:56 waiting at gates (Spec gate waited overnight) |
| Time per stage | spec <1m, plan <1m, implement ~2m, verify <1m (agent time, gate waits excluded) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 3 |
| Review first-pass rate | 1/1 (100%) |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 5/5 |

## Reflections
1. Did the result match what you meant? Not asked yet.
2. Where did you have to step in, and why? None.
3. One change that would have prevented that? n/a

## Proposed improvements
- Running the doc itself caught two wrong claims (missing backticks in an error example, an
  unexecuted "in sync" claim). Executable docs are worth the format constraint: consider running
  `run-tutorial.sh` in CI (follow-up in the PR).
- Plan gate `presented_at` equals Spec `approved_at` when the plan is written in the same turn.
  Fine, but the architect's own time then shows as zero. Record `presented_at` after the plan
  file is written, not at the start of the turn.
