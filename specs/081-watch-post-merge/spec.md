# Spec: watch post-merge verify and the retro's After delivery section

Ticket: gh:81 · Size: standard · Status: draft

## Problem
`watch` currently reports `merged` and `closed` and stops (watch.md), so a run never learns whether
its criteria still hold on the default branch, never records time to merge, and its retro stops at
deliver. The roll-up (`retro_report.py`) has nothing to read about what happened after the PR opened.
This is the last step of campaign gh:77 (design: `docs/post-deliver.md`).

## Goals
- On merge, re-verify `spec.md`'s criteria on the default branch and surface regressions.
- End a closed, unmerged PR cleanly and record every outcome from timestamps, never estimates.
- Close the learning loop: retro After delivery section, roll-up columns, an offline eval.

## Non-goals
- Opening a ticket, PR, or comment automatically for a regression (a follow-up is only suggested).
- Polling, daemons, or reacting to merges outside `/spec-resume` or `/work <ref>`.
- Reverting, fixing, or re-running tasks after a merge.
- Changing the `pr_status` contract for real connectors beyond the optional fields named here.

## Acceptance criteria
- **AC1**: Given a run at `stage: watch` and a `pr_status` of `merged`, when the resume pass runs, then it checks out the default branch (`state.base`) at the merge commit, runs the verifier over `spec.md`'s criteria, writes `verify-merged.md` (same shape as `verify.md`, headed with the merge sha), and sets `watch.merged_at`, `watch.post_merge` and `stage: done`.
- **AC2**: Given `pr_status` has no usable merge commit (no gh, or the sha does not resolve locally), when post-merge verify runs, then it verifies the local tip of `state.base`, says so in `verify-merged.md`, and never invents a sha. With gh, the merge commit is the PR's merge commit sha.
- **AC3**: Given a criterion passed in `verify.md` and fails in `verify-merged.md`, when the pass finishes, then `watch.post_merge` is `regression`, each such criterion is named in the report with a suggested follow-up ticket title and body, and nothing is opened, pushed, or posted.
- **AC4**: Given every criterion passes on the merge commit, then `watch.post_merge` is `pass`; given verify cannot run (checkout or tests unavailable), then `unverified` with the reason, never `pass`.
- **AC5**: Given `pr_status` is `closed` (unmerged), when the resume pass runs, then `stage` is `done`, `watch.outcome` is `abandoned`, the report says `done (abandoned)`, and no post-merge verify runs. `watch.outcome` is `merged` after AC1. `stage` gains no new value.
- **AC6**: Given the PR was opened and later merged, when `watch` ends, then `metrics.time_to_merge` (minutes) equals `watch.merged_at` minus `metrics.pr_opened_at`, both UTC timestamps; if either is missing it is left unset (unknown, never zero or estimated). `metrics.pr_opened_at` is a new field, set from `date -u` when `link_pr` records `ticket.pr`; `watch.merged_at` is the `pr_status` `merged_at`.
- **AC7**: Given `watch` ends (merged or abandoned), when the run finishes, then `retro.md` has an **After delivery** section appended once (a re-run does not duplicate it) listing: CI failures (own and external counts), review rounds, what reviewers caught that the run's own reviewers missed (or "none"), and the post-merge result. `templates/retro.md` carries the section skeleton.
- **AC8**: Given runs with and without the new fields, when `retro_report.py` runs, then each run row shows `Outcome` (merged/abandoned/unknown), `Post-merge` (pass/regression/unverified/unknown), `Time to merge` (min), `Review rounds` and `CI failures`; aggregates add average time to merge (n shown), and counts of merged, abandoned, and regression runs. Missing fields are `unknown`, never 0. `--json` includes the same fields and `schema_version` is bumped. Tests are written first.
- **AC9**: Given the sandbox merged fixture (`examples/sandbox/pr_status/merged.json`, extended additively with `merged_at` and `merge_commit_sha`) and a synthetic run folder, when `evals.py check` runs the new sandbox case, then it asserts `stage: done`, `watch.outcome: merged`, `watch.merged_at` set, `watch.post_merge` set, `metrics.time_to_merge` present, a `verify-merged.md` exists, and `retro.md` contains `## After delivery`; existing fixtures and cases still pass.
- **AC10**: Given the work is delivered, then `watch.md`, `state.md`, `lifecycle.md` (if it names `merged`/`closed`) and `docs/efficiency.md`'s report section describe the above, and `docs/roadmap.md` moves the watch item to Done.

## Constraints
- Offline-only validation; `merged.json` changes are additive so children 2 and 3 fixtures and evals keep passing.
- The default branch checkout must not touch the user's uncommitted work (resume's clean-tree rule applies) and never force or push.
- Verify output is untrusted-data safe: no secrets in `verify-merged.md`. Scripts stay stdlib-only.

## Requirement changes

### Area: run-lifecycle
#### MODIFIED: Watch stage for CI failures
For `delivery: normal` runs on a connector with `pr_status`, `stage` SHALL pass through `watch` between `deliver` and `done`; resuming at `watch` SHALL handle changes since `watch.checked_at`; a failed check SHALL be recorded as `external` or `own` as before; a `merged` PR SHALL end `watch` with post-merge verify and a `closed` unmerged PR SHALL end it as `done` with `watch.outcome: abandoned`; `local-only` runs and connectors without `pr_status` SHALL skip `watch`. (AC1, AC5)
#### MODIFIED: Post-deliver state
`state.json` SHALL record `watch.checked_at`, `watch.ci_failures`, `watch.merged_at`, `watch.post_merge`, `watch.outcome`, `metrics.post_deliver_retries`, `metrics.pr_opened_at` and `metrics.time_to_merge` (from timestamps only), documented in `state.md`. (AC6)
#### ADDED: Post-merge verify
On merge, the run SHALL verify `spec.md`'s criteria on the default branch at the merge commit into `verify-merged.md`, report a criterion that passed on the branch and fails there as a regression with a suggested follow-up, and SHALL NOT open anything automatically. (AC1, AC2, AC3, AC4)
#### ADDED: Retro After delivery section
When `watch` ends, `retro.md` SHALL gain one appended **After delivery** section covering CI failures, review rounds, reviewer catches the run missed, and the post-merge result. (AC7)

### Area: metrics-report
#### MODIFIED: Per-run and grouped aggregate metrics
The system SHALL report duration, gate rework, first-pass rate, retries, interventions, wave stats, and criteria passed as before, and also outcome, post-merge result, time to merge, review rounds, and CI failures per run, with average time to merge and merged, abandoned, and regression counts in the aggregates, missing values unknown. (AC8)

### Area: evals
#### ADDED: Merged watch eval
A sandbox eval SHALL grade the merged path offline from the merged fixture, checking post-merge fields, `verify-merged.md`, and the retro's After delivery section. (AC9)

## Open questions
1. Under the fixture (no remote) a `merge_commit_sha` cannot resolve locally; AC2 falls back to the local `state.base` tip. Is that acceptable, or should the fixture eval skip the checkout and only grade state? *Matters for how real the eval is.*
2. `metrics.pr_opened_at` does not exist today (nothing records the PR open time). Prefer the connector's PR `created_at` over the local clock when available? *Affects time_to_merge accuracy.*
3. Should a regression set `blocked` or only be reported? Spec assumes report only and `stage: done`. *Decides whether the run is left open.*

## Proposed split
(large only)
