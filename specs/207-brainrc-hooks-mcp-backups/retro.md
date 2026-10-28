# Retro: 207-brainrc-hooks-mcp-backups

Ticket: gh:207 · Size: standard · PR: https://github.com/brainrc/brainrc/pull/233

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | see state.json `metrics` |
| Time per stage | see `metrics.stage_started_at` |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 6 (T1-T5, F1); 1 parallel wave (width 3; 10 task-min in 4 wall-min) |
| Review first-pass rate | T1-T5 reviews passed first time except T3 (attempt 2, caused by the engine's brief) |
| Retries | 1 (T3) |
| Interventions | 1 (owner approved the plan's callouts after the auto hard stop) |
| Criteria passed | 13/13 |

## Reflections
1. skipped
2. Auto stopped at the Plan gate on its callouts; the owner approved and the run continued in auto.
3. skipped

## Proposed improvements
- Engine: copy contract rules (here AC7's "resolved home wins") verbatim from the plan into dispatch briefs instead of paraphrasing; the paraphrase caused T3's retry.
- Engine: commit a `review: each` task only after its review (T2 was committed first by mistake).
- Worktree briefs: save run logs outside `specs/` in the worktree, or teach worktree_fence.py to ignore `specs/<slug>/.runs/`.
- Verify: always also run the suite with `XDG_CONFIG_HOME` set, as CI runners do.
