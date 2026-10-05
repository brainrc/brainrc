# Retro: 007-example-pack

Ticket: gh:7 · Size: standard · PR: https://github.com/bxker/ai-config/pull/28

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:15, including two gate waits |
| Time per stage | spec 6m (incl. gate wait), plan 2m (incl. gate wait), implement 2m, verify 1m |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 2 |
| Review first-pass rate | 1/1 (100%) |
| Retries | 0 |
| Interventions | 1 (user asked where the work was at the Deliver gate) |
| Criteria passed | 6/7 locally, AC5 pending the PR's `validate` job |

## Reflections
1. Did the result match what you meant? Not asked yet.
2. Where did you have to step in, and why? At the Deliver gate the summary listed only
   `specs/` under Artifacts, so the code changes looked missing.
3. One change that would have prevented that? Proposed below.

## Proposed improvements
- `lifecycle.md` § Gate presentation: the Deliver gate should list changed files outside
  `specs/` (`git diff --stat <base>...HEAD -- . ':!specs'`) before the spec artifacts, so the
  code is the first thing the user sees.
- `sizing.md`: this ticket scored `standard` on file count alone (8 new example files, no real
  design choice). A note that new self-contained example or doc files weigh less than edits to
  existing code would let tickets like this run as `small` with one gate.
