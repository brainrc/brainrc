# Retro: 216-work-auto-mode

Ticket: gh:216 · Size: standard (resized from large at the Spec gate) · PR: https://github.com/brainrc/brainrc/pull/227

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:48 total, of which 31 min waiting at gates (includes two worker restarts) |
| Time per stage | recorded starts: intake 03:01Z, spec 03:01Z, plan 03:03Z, implement 03:25Z, verify 03:35Z, document 03:39Z, deliver 03:39Z |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 6 (T1-T4, F1-F2; no parallel waves: fallback mode) |
| Review first-pass rate | 1/3 (33%) |
| Retries | 0 |
| Interventions | 0 |
| Review context | shared |
| Criteria passed | 8/8 |

## Reflections
1. skipped (not answered yet)
2. skipped (not answered yet)
3. skipped (not answered yet)

## Proposed improvements
- Review caught a case (sandbox-014) that would fail a correct run, because the stop it grades happens after implement. architect role: for each eval case, name the stage the graded event happens at, and check only artifacts that exist by then.
- The E2 landing showed stacked PRs merged into their bases get stranded. campaign.md § Retarget rule could add: the stack's PR bodies say "Retarget to `main` before merging" (already), and the engine retargets each later PR only after its predecessor is on main; consider opening later PRs with base `main` plus a "merge after #X" note instead.
- Fallback mode again (role agents not installed in this cloud session): fresh-context reviews need the agents installed (`aicfg apply`) in the session image.
