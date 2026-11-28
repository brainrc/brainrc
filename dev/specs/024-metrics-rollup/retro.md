# Retro: 024-metrics-rollup

Ticket: gh:24 · Size: standard · PR: https://github.com/bxker/ai-config/pull/82

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:51 total = 0:37 agent + 0:14 waiting at gates (the first Spec-gate wait was lost when the run moved from gh:76 to gh:24, so waiting is undercounted) |
| Time per stage | spec 12, plan 6, implement 15, verify 2 (agent time, gate waits excluded; spec includes the duplicate-ticket move and the #24 revision) |
| Gate rework (spec / plan / deliver) | 1 / 0 / 0 |
| Tasks | 8: T1–T6 plus fix tasks F1, F2 (parallel waves: 2, widest 2; 6.3 task-min in 3.7 wall-min) |
| Review first-pass rate | 1/2 (50%) |
| Retries | 0 |
| Interventions | 1 (the user caught that gh:76 duplicated gh:24) |
| Criteria passed | 19/19 (AC14 stub-verified only) |

## Reflections
Ask the user these three; record answers verbatim (or "skipped"):
1. If the user wrote the ticket: did the result match what you meant? Otherwise (someone
   else's issue): would you ship this as-is, and if not, what's missing?
   Answer: skipped (not yet answered)
2. Where did you have to step in, and why?
   Answer: skipped (not yet answered). From the run: the engine opened gh:76 without searching, and it duplicated gh:24.
3. One change to a skill, agent, or rule that would have prevented that?
   Answer: skipped (not yet answered)

## Proposed improvements
- Intake: before creating a ticket (or running on free text), search open issues for the same work. The engine created gh:76 while gh:24 already tracked it. A duplicate check in lifecycle § 0, and in the ticket connectors' create path, would have caught it.
- Parallel waves need a contract note in the dispatch. T2 changed `blocked_stops` to include the current block while T3, in parallel, assumed it didn't. Result: a double count (F1), then a second double count found in review (F2). When two wave tasks share a data shape, the architect should pin it in plan.md and both dispatches should quote it.
- Keep the first presentation time when a gate is re-presented (append, don't reset `metrics.gates.<gate>`). This run lost about 10 minutes of Spec-gate wait.
- Integration smoke after each wave lands (run the real CLI on real data). It caught the negative-duration bug before review did.
- Follow-up: run `--ccusage` once against a real ccusage install; add the `retro_*` modules to `docs/install.md`.
