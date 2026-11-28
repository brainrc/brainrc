# Retro: 025-parallel-tasks

Ticket: gh:25 · Size: standard · PR: https://github.com/bxker/ai-config/pull/48

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 4 (T4 added at the Plan gate on request; no parallel waves: inline run) |
| Retries | 0 |
| Interventions | 1 (owner asked for clickable gates) |
| Criteria passed | 6/6 (issue criterion 3 deferred to an E2E run) |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? Typing "approve" at every gate; now gates use a
   multiple-choice question where the harness has one.
3. One change that would have prevented that? Done in this PR (T4).

## Proposed improvements
- The real landing run found `git worktree remove` failing on staged changes. Prose-only
  engine steps should get a scripted dry run like this one whenever they contain commands.
