# Retro: 078-pr-status-connector

Ticket: gh:78 · Size: standard · PR: https://github.com/bxker/ai-config/pull/84

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:18 to drafts = 0:13 agent + 0:05 waiting at Spec/Plan gates; then waited for the campaign's stack Deliver gate (children 2–4), approved 2026-10-24 |
| Time per stage | spec 3, plan 5, implement 6, verify 1 (gate waits included in spec/plan) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 4 (parallel waves: 1, widest 4; 8.2 task-min in 3.5 wall-min) |
| Review first-pass rate | 1/2 (50%) |
| Retries | 1 |
| Interventions | 0 |
| Criteria passed | 9/9 |

## Reflections
Ask the user these three; record answers verbatim (or "skipped"):
1. Did the result match what you meant? (not yet answered)
2. Where did you have to step in, and why? (not yet answered)
3. One change to a skill, agent, or rule that would have prevented that? (not yet answered)

## Proposed improvements
- T2's first attempt replaced the approved two-call design (AC3) with one GraphQL query. The implementer dispatch could quote the AC text verbatim when a task's criteria name a specific command.
- First child of the first real ordered campaign: the campaign schema has no member status for "verified, waiting for the stack Deliver gate" (`verified` was used). Add it to `campaign.md`.
