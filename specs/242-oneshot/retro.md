# Retro: 242-oneshot

Ticket: gh:242 · Size: standard · PR: https://github.com/brainrc/brainrc/pull/258

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | about 2 days wall time, mostly waits and three container restarts; agent time several hours |
| Time per stage | see state.json `metrics.stage_started_at` |
| Gate rework (spec / plan / deliver) | 1 / 0 / 0 (the owner split the hard stops after the security review) |
| Tasks | 6 + 5 fix tasks (one parallel wave of 2, in nested task worktrees) |
| Review first-pass rate | see state.json `metrics.reviews` |
| Retries | 1 (T2) |
| Interventions | 1 (owner decision on tainted vs benign stops) |
| Criteria passed | 11/11 against fake runs or instruction text; real `--oneshot` runs not run |

## Reflections
1. skipped
2. skipped
3. skipped

## Proposed improvements
- The first run in its own worktree (#255) worked: the owner's checkout stayed on its branch with a clean status for the whole run, and three container restarts lost no work, because the worktree is outside `/tmp`. Only in-flight subagents were lost.
- A security review at the instruction level caught a design flaw (pushing tainted branches) that the spec and plan had approved. For engine changes that touch outward actions, run the security reviewer on the spec, before the plan.
- Eval cases written by the same agent as the fake runs that grade them were too lenient: the batch review found eight ways a broken run could pass. A case task should include "write one fake run that should fail each check" as a requirement, not as a review finding.
- Subagents lost to container restarts: two attempts died before editing. For short doc tasks, the engine doing the work inline was faster than re-dispatching.
- Records written after the PR opened missed main again (#255). This run wrote its retro before the PR opened. #245 should make that the rule.
