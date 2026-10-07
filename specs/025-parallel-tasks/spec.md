# Spec: Parallel implement waves in subagent mode

Ticket: gh:25 · Size: standard (engine prose in 5 files, a sandbox ticket and eval case; design choices) · Status: draft

## Problem
Implement runs tasks one at a time even when they touch different files, so a plan with
independent slices takes the sum of their times. `efficiency.md` forbids parallel writers
today, for a good reason: implementers sharing one working tree run the tests against each
other's half-written changes.

## Design (choices to confirm)
1. **Isolation: one git worktree per parallel task, created by the engine.**
   `git worktree add <tmp>/spec-agent/<slug>/<task> HEAD`, outside the repo so test runners
   never discover it, passed to the subagent as its working directory. Harness-neutral (any
   harness with subagents and Bash), and each implementer's test runs see only its own change.
   A shared tree with only the scope fence is rejected: concurrent test runs interfere.
2. **Eligibility: a "wave" is the todo tasks whose `after:` dependencies are done and whose
   `files` are pairwise disjoint.** New optional `after: T1` line per plan task; the architect
   adds it when one task needs another's code. Tasks with `agent: test-writer`, or `review: each`
   on security triggers, still run alone.
3. **Landing: the engine lands each task in plan order.** In the task's worktree it stages
   everything, checks the staged paths ⊆ `files` (else a failed attempt, as today), exports a
   patch to `.runs/<task>.patch`, applies it to the main tree with `git apply`, runs the
   scoped tests there, and commits. Disjoint files mean patches can't conflict; a patch that
   fails to apply is a failed attempt. Worktrees are removed after landing.
4. **Cost guard: at most 2 tasks per wave for `standard`, 3 for `large`** (large splits first,
   so this rarely applies). `inline` and `fallback` modes never run waves.
5. **State:** several tasks may be `in_progress` at once; each records `wave` (1, 2, …) and,
   while running, `worktree`. `metrics.waves` = `{ "count", "max_width", "task_minutes",
   "wall_minutes" }`, from `date -u` stamps per task, so the retro can show the saving.

## Acceptance criteria
- **AC1** `references/efficiency.md` has a "Parallel waves" design note covering choices 1–5,
  and its "Never run writers in parallel" line becomes "only in isolated worktrees (below)".
- **AC2** `SKILL.md` Implement stage dispatches waves in `subagent` mode per choices 2–4 and
  lands them per choice 3; one-at-a-time behaviour is unchanged otherwise.
- **AC3** `templates/plan.md` and `agents/architect.md` document `after:`; `references/state.md`
  documents `tasks[].wave`, `tasks[].worktree`, `metrics.waves`; `templates/retro.md` shows
  the wave saving (task-minutes vs wall-minutes).
- **AC4** Sandbox ticket `examples/sandbox/tickets/003-two-features.md` with two independent
  slices (a new `farewell.py`, and a `--version` flag in `greet.py`), plus
  `evals/cases/sandbox-003.toml` checking both features, all criteria, and
  `metrics.waves.max_width == 2`.
- **AC5** The landing steps are tested for real once: two worktrees with disjoint edits,
  patches applied to the main tree in order, plus a stray-file patch rejected (recorded in
  verify.md).
- **AC6** VERSION 0.3.13, CHANGELOG; `validate` and tests pass.

## Not in this ticket
- The end-to-end subagent-mode run of ticket 003 that measures the real saving (the issue's
  third criterion). It needs the agents installed and a session where you approve its gates,
  like #18. I'll propose running it in this session after merge, as a separate step.

## Open questions
1. Run the ticket-003 end-to-end here after merge (uses subagents, so more tokens), or leave
  it for a later session?
