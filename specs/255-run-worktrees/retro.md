# Retro: 255-run-worktrees

Ticket: gh:255 · Size: standard · PR: https://github.com/brainrc/brainrc/pull/257

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | about 1:45 total, most of it agent time; waits at gates were short (owner replied quickly) |
| Time per stage | spec about 2, plan about 3, implement about 45, verify about 5 (minutes, agent time) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 + 3 fix tasks (parallel waves: 3, widest 2; task-minutes and wall-minutes in state.json `metrics.waves`) |
| Review first-pass rate | 2/3 (67%): T1 review clean of CRITICAL/HIGH, batch review 2 HIGH, fix re-review clean |
| Retries | 1 (T1 review findings) |
| Interventions | 0 |
| Criteria passed | 9/12 (AC1, AC3, AC7 not run end to end; git-level parts verified) |

## Reflections
1. skipped
2. skipped
3. skipped

## Proposed improvements
- A test-writer or implementer's stub-phase test committed into the real repo, because empty script output became `Path("")`, which is cwd. Add a rule to the implementer role and the scripting skill: tests that run git or write files must assert that their target path lies inside the test's temp root before acting, and must strip `GIT_*` from subprocess environments.
- The plan grouped a `review: each` task into a wave, which the wave rules forbid. The architect role should apply efficiency.md § Parallel waves (review-each and test-writer tasks run alone) when writing the waves line.
- Task worktrees inherit `.runs/` logs, which `tests/test_old_names.py` scans. Twice this produced a confusing suite failure. Either have the old-names test skip `specs/*/.runs/`, or tell implementers in wave dispatches to keep logs outside the worktree.
- The batch review caught cross-file drift (campaign base, resume recovery) that per-file tasks missed. When a plan changes a concept used across references, add a final "consistency sweep" task that greps the references for the old concept.
