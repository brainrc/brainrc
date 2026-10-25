Add watch stage for CI failures with a Push gate

## Why
After Deliver, red CI on a run's PR was fixed by hand and never counted in the run's metrics. This adds a `watch` stage that reads the PR's checks on `/spec-resume` or `/work <ref>`, and holds every push of a fix behind approval.

## What changed
- `delivery: normal` runs on a connector with `pr_status` enter `watch` after the PR opens. `local-only` runs and connectors without `pr_status` still end at `done`.
- Resuming at `watch` reads `pr_status` once and handles only what changed since `watch.checked_at`. With nothing changed it reports that and touches nothing else. No loop or daemon runs.
- A failed check is summarized into `.runs/`. If it is also red on the base branch, or its log names no file in the diff, it is recorded as `external` and the run stops with a one-line note. Otherwise it is recorded as `own` with fix task `C<n>`, which runs implement → review under the normal retry budget.
- A pushed fix needs an approved Push gate that shows the diff stat, the commits, and the check it fixes. A rejected or unanswered gate leaves the commits local.
- `state.json` gains `stage: watch`, `watch`, `gates.push`, `gate_rework.push`, and `metrics.post_deliver_retries`. `state.md`, `lifecycle.md`, and `docs/post-deliver.md` describe them.
- `SPEC_PR_STATUS_FIXTURE` reads `pr_status` from a fixture file instead of the connector. It is honored only in a copy with no git remote.
- `evals.py` `state` checks accept list indexes (`watch.ci_failures.0.cause`). New sandbox eval `sandbox-005` grades the red-CI path offline.
- Not in this PR: review comments (#80), merged and closed handling, and post-merge verify (#81).

Blast radius: runs without `pr_status`, and `local-only` runs, end at `done` as before. Skill text changes in `SKILL.md`, `lifecycle.md`, `guardrails.md`, and `work/SKILL.md`. `metrics.retries` is unchanged.

## Acceptance criteria
- [x] AC1: `stage` moves to `watch` with `checked_at` set, verified by reading `references/watch.md` § Enter
- [x] AC2: `local-only` and no-`pr_status` runs go to `done`, verified by reading `watch.md` § Enter and `lifecycle.md`
- [x] AC3: resume reads once and reports "no change", verified by reading `watch.md` § Resume pass
- [x] AC4: log summary saved under `.runs/`, verified by reading `watch.md` § CI failure
- [x] AC5: `external` cause stops the run with no task, verified by reading `watch.md` § CI failure
- [x] AC6: `own` cause creates `C<n>` with the retry budget, verified by reading `watch.md` and `state.md`
- [x] AC7: Push gate before any push, verified by reading `watch.md` § Push gate and `guardrails.md`
- [x] AC8: schema and docs updated, verified by reading `state.md`, `lifecycle.md`, and `docs/post-deliver.md`
- [x] AC9: `sandbox-005` passes on a synthetic good run and fails on the external and approved-gate runs, verified by `WatchRedCiCaseTest` and `evals.py check`
- [x] AC10: validate passes, 328 tests pass, dotted-index pass and fail cases, verified by `CheckTest.test_state_numeric_index_segment`

Spec change after approval: AC9's fixture path is the sandbox-relative `pr_status/red-ci.json`.

The watch procedure is skill text. No run executed it end to end, and no live `gh` call was made.

## How to verify
```
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
python3 -m unittest -v tests.test_evals.WatchRedCiCaseTest tests.test_evals.CheckTest.test_state_numeric_index_segment
```

## Follow-ups
- `SPEC_PR_STATUS_FIXTURE` is read only by prose. No check runs the fixture path.
- `sandbox-005` does not grade the summary file's content (the plan's check was dropped), and no check covers AC9's "no PR created" condition.
- `watch.md` says "the raw log stays in `.runs/`", which can be read as keeping the raw log. The summary is what AC4 requires. Clarify the wording.
- The `gh pr checks`, `gh run view`, and `gh api` calls in `watch.md` have not run against a live PR.

Spec: `specs/079-watch-ci-failures/spec.md` · Plan: `specs/079-watch-ci-failures/plan.md`
Closes #79. Part of #77 (campaign gh:77, 2 of 4, after #<PREDECESSOR_PR>).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01BdiJDGmXUuJTx5qC4ADnaF
