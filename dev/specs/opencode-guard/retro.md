# Retro: opencode-guard

Ticket: gh:50 · Size: standard · PR: https://github.com/bxker/ai-config/pull/61

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 4/4 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? When the real trigger needs a model, load the
   code inside the real runtime with a probe; it caught nothing here but proves the path.

## Notes
- Worker restarts twice this run; the spec and deliver approvals were recorded at the first
  command after each restart, not estimated.
- OpenCode's `!` shell (and `/session/:id/shell`) bypasses plugin hooks.
