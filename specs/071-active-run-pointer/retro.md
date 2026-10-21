# Retro: 071-active-run-pointer

Ticket: gh:71 · Size: standard · PR: https://github.com/bxker/ai-config/pull/72

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:21 total = 0:15 agent + 0:06 waiting at gates |
| Time per stage | spec 1, plan 2, implement 8, verify 2 (agent time, gate waits excluded; plan includes folding the Spec-gate answers into spec.md) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 3 (parallel waves: 0; every task was `review: each`, which runs alone) |
| Review first-pass rate | 3/4 (75%) |
| Retries | 1 |
| Interventions | 0 |
| Criteria passed | 12/12 |

## Reflections
Ask the user these three; record answers verbatim (or "skipped"):
1. If the user wrote the ticket: did the result match what you meant? Otherwise (someone
   else's issue): would you ship this as-is, and if not, what's missing?
   Answer: skipped (not yet answered)
2. Where did you have to step in, and why?
   Answer: skipped (not yet answered)
3. One change to a skill, agent, or rule that would have prevented that?
   Answer: skipped (not yet answered)

## Proposed improvements
- Add a `Runs:` line to the dispatch prompt in `handoff.md` (`specs/<slug>/.runs/`). T2's implementer wrote its logs to a repo-root `.runs/` until told otherwise.
- Architect: default doc-only tasks to `review: batch`. T3 (docs) was independent of T1/T2 but `review: each` kept it out of a parallel wave, so this standard run had no waves at all.
- The T3 HIGH (a relative `specs/<slug>` path) is a pattern: any doc that tells the engine to pass a path to a script outside the repo should say "absolute". Worth one line in SKILL.md § Always.
- Follow-up from review: make `active_run.py write` warn when the run directory doesn't exist, and add a test for the `RuntimeError` path.
