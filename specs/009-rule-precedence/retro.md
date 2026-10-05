# Retro: 009-rule-precedence

Ticket: gh:9 · Size: standard · PR: https://github.com/bxker/ai-config/pull/31

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | about 1h40 wall clock, mostly waiting at gates |
| Time per stage | implement ~10m, verify ~2m (spec and plan dominated by gate waits) |
| Gate rework (spec / plan / deliver) | 1 / 0 / 0 |
| Tasks | 4 |
| Review first-pass rate | 3/3 (100%) |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 8/8 |

## Reflections
1. Did the result match what you meant? Not asked yet.
2. Where did you have to step in, and why? Spec rework: the user decided every PR should bump
   VERSION, and the validate check for it was folded into this ticket.
3. One change that would have prevented that? None needed. A policy decision, not a miss.

## Proposed improvements
- Parallel PRs that each bump VERSION will conflict. spec-agent's Deliver stage could check
  for other open PRs touching `VERSION`/`CHANGELOG.md` and say which merges first.
