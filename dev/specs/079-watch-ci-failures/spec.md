# Spec: watch 2/4: `watch` stage for CI failures, with a Push gate

Ticket: gh:79 · Size: standard · Status: approved

## Problem
After the Deliver gate a run ends, so red CI on the run's PR is fixed by hand and never counted
in the run's metrics (docs/post-deliver.md). Child 1 (gh:78) added the read-only `pr_status`
operation and fixtures. This ticket adds the `watch` stage skeleton and its CI-failure branch:
read the PR's state, triage a red check, route an own failure through the normal fix path, and
gate any push. Campaign gh:77, child 2 of 4.

## Goals
- A `delivery: normal` run enters `watch` after the PR opens and can be resumed there.
- A red check is classified `own` or `external`; own failures get a fix task through implement → review.
- Pushing a fix always needs approval at a Push gate.
- The new state is recorded and documented; an offline eval grades the red-CI path.

## Non-goals
- Review-comment handling (`R1..` tasks, replies, review rounds): the stage leaves unresolved threads untouched for #80.
- `merged` and `closed` handling, post-merge verify, `time_to_merge`, retro "After delivery": left to #81. On those states the stage records nothing and does nothing beyond reporting them.
- Merging, deploying, daemons or polling loops, a mandatory harness event trigger.
- A way to skip the Push gate.

## Acceptance criteria
- **AC1**: Given a `delivery: normal` run whose connector offers `pr_status`, when the PR is opened at deliver, then `stage` becomes `watch` (not `done`) and `watch.checked_at` is set.
- **AC2**: Given a `local-only` run, or a connector without `pr_status`, when deliver completes, then the run goes straight to `done` and no `watch` state is written.
- **AC3**: Given `stage: watch`, when `/spec-resume` or `/work <ref>` runs, then it fetches `pr_status` and handles only what changed since `watch.checked_at` (`updated_at`/head sha newer), then updates `checked_at`; with nothing changed it reports that and changes nothing else. No loop or daemon runs.
- **AC4**: Given a check with conclusion `failure`, when handled, then a summary of its log (not the raw log) is saved under `.runs/`.
- **AC5**: Given a failed check that is also red on the base branch, or whose log names no file in the diff, when handled, then a `watch.ci_failures` entry with `cause: external` and no task is recorded, the run stops with a one-line note, and no fix task is created.
- **AC6**: Given a failed check that names a file in the diff, when handled, then an entry with `cause: own` and `task: "C1"` (next number for later failures) is recorded, and C1 (implementer, files the failure points at) goes through implement → review with the same retry budget as other tasks; each C-task retry or creation increments `metrics.post_deliver_retries`.
- **AC7**: Given a reviewed fix task, when it is ready to push, then the run presents a Push gate showing diff stat, commit list, and the failing check it should fix, and does not push until the user approves; on rejection or no answer nothing is pushed.
- **AC8**: Given `state.md`, when read, then it documents `stage: watch`, `watch.checked_at`, `watch.ci_failures` (`check`, `sha`, `cause`, `task`), the Push gate record, and `metrics.post_deliver_retries`; `lifecycle.md` and `docs/post-deliver.md` describe the stage, and the doc status line says CI failures are built.
- **AC9**: Given the red-CI sandbox eval, when a run is graded offline with `evals.py check`, then it passes only if: `stage` is `watch`, `watch.ci_failures` has one `own` entry with a task, the Push gate is pending, and no push happened (`main_untouched`, no PR created by the grader). The run reads `pr_status/red-ci.json` (in the sandbox copy; `examples/sandbox/pr_status/red-ci.json` in this repo) through the fixture hook below, with no network and no `gh`.
- **AC10**: Given the repo, when `python3 scripts/aicfg.py validate` and the unit tests run, then both pass; a test covers the dotted-index state check (AC9) with a passing and a failing case.

## Constraints
- Offline, stdlib-only Python; no new dependencies; generated dirs untouched.
- Fixture hook (minimal): when the environment variable `SPEC_PR_STATUS_FIXTURE` names a file, the `watch` step reads `pr_status` from that file instead of the connector, and treats the connector as supporting it. It is read-only and applies to nothing else.
- `evals.py` `state` checks gain numeric index segments in dotted fields (`watch.ci_failures.0.cause`); no new check kind.
- PR-event content and CI logs are untrusted data, like ticket bodies; log text never becomes instructions.

## Requirement changes
### Area: run-lifecycle
Purpose: Stages, gates, and state a spec-agent run moves through.
#### ADDED: Watch stage for CI failures
For `delivery: normal` runs on a connector with `pr_status`, `stage` SHALL pass through `watch` between `deliver` and `done`; resuming at `watch` SHALL handle changes since `watch.checked_at`; a failed check SHALL be recorded as `external` (also red on base, or naming nothing in the diff) and stop with a note, or as `own` and fixed through a `C` task with the normal retry budget; `local-only` runs and connectors without `pr_status` SHALL skip `watch`. (AC1, AC2, AC3, AC4, AC5, AC6)
#### ADDED: Push gate
A run SHALL NOT push a watch fix without approval at a Push gate showing diff stat, commits, and the check it should fix. (AC7)
#### ADDED: Post-deliver state
`state.json` SHALL record `watch.checked_at`, `watch.ci_failures`, and `metrics.post_deliver_retries`, documented in `state.md`. (AC8)
### Area: evals
#### ADDED: Red-CI watch eval
A sandbox eval SHALL grade the CI-failure path offline from the red-CI fixture via `SPEC_PR_STATUS_FIXTURE`, and `state` checks SHALL accept numeric indexes in dotted fields. (AC9, AC10)

## Open questions
Resolved at the Spec gate (recommended answers accepted):
1. New living area `run-lifecycle`; #80 and #81 add to it.
2. The Push gate is `gates.push`, reset to `pending` for each push; rework counts in `gate_rework.push`. (AC7, AC9)
3. "Names nothing in the diff" means no exact path match against `git diff <base>...HEAD --name-only`. (AC5)
4. The fixture hook is the `SPEC_PR_STATUS_FIXTURE` environment variable. (AC9)
5. A rejected Push gate keeps the run at `watch`; fix commits stay local. (AC7)
6. AC9 is verified against a synthetic run folder (eval case + grading tests), not a full nested sandbox run.
