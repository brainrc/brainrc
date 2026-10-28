# Retro: 208-brainrc-plugin-namespace

Ticket: gh:208 · Size: standard · PR: https://github.com/brainrc/brainrc/pull/234

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | see state.json `metrics` |
| Time per stage | see `metrics.stage_started_at` |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 (the engine sent the spec back once before the gate to add Claude Code detection) |
| Tasks | 5 (T1-T4, F1); 1 parallel wave (T1, T2) |
| Review first-pass rate | T2 needed a second attempt (1 HIGH); batch passed |
| Retries | 1 (T2) |
| Interventions | 1 (owner approved the plan's callouts and chose the patch bump) |
| Criteria passed | 12/12 |

## Reflections
1. skipped
2. Auto stopped at the Plan gate (plugin-rename contract, bump choice); the owner chose patch.
3. skipped

## Proposed improvements
- analyst role: when a criterion needs another tool's on-disk state, look up the tool's documented location before scoping it out; the first spec dropped Claude Code detection.
- code-reviewer found that `json.loads` can raise RecursionError on hostile input; worth a line in the scripting skill's checklist for any parser of files the user's other tools write.
- The changelog policy (minor for a breaking pack contract) conflicts with a pending removal version; the release workflow could warn when a minor bump would reach `SHIM_REMOVED_IN`.

## After delivery
- Outcome: merged
- Merged at: 2026-10-28T17:05:54Z · Time to merge: 0 min (merged right after CI)
- Post-merge verify: pass (see `verify-merged.md`)
- CI failures: 0 own / 0 external
- Review rounds: 0
- Caught by reviewers, missed by the run's own: none
- Follow-up title: none
- Follow-up body: none
