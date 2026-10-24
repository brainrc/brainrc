Verify merged PRs after merge and record watch outcomes

## Why
`watch` stopped at `merged` or `closed`. A run never learned whether its criteria still held on the default branch, never recorded time to merge, and its retro ended at deliver. This is the last step of campaign gh:77. Merging this PR finishes the watch stage.

## What changed
- A merged PR is verified at its merge commit. `watch` runs the verifier in a detached worktree, writes `verify-merged.md`, and sets `watch.post_merge` to `pass`, `regression`, or `unverified`. A regression names each failing criterion and prints a suggested follow-up. Nothing is opened, pushed, or posted.
- If the merge commit does not resolve locally, the verify uses the local tip of the base branch and says so in the file.
- A PR closed without merging ends the run as `done (abandoned)`. No verify runs.
- `metrics.time_to_merge` is in minutes, from `metrics.pr_opened_at` to `watch.merged_at`. It stays unset when either value is missing.
- `retro.md` gets one `## After delivery` section when `watch` ends. A re-run does not add a second one.
- `scripts/retro_report.py` shows Outcome, Post-merge, Time to merge, Review rounds, and CI failures per run. Aggregates add average time to merge (with `n`) and merged, abandoned, and regression counts. Missing values show `unknown`. `--json` is `schema_version` 2.
- Sandbox eval `sandbox-007` grades the merged path offline, on a synthetic run folder.
- Docs (`post-deliver.md`, `efficiency.md`, `state.md`, `watch.md`, `spec-agent.md`) describe the above. The roadmap item moves to Done.

Blast radius: runs without `pr_status` and `local-only` runs still end at `done`. Runs without the new fields read as `unknown`, never 0.

## Acceptance criteria
- [x] AC1: merged PR verified at the merge commit, `verify-merged.md` written, fields set, `stage: done` last, verified by reading `watch.md` § Merged or closed and by `sandbox-007` on a synthetic run
- [x] AC2: unresolved sha falls back to the base tip and says so, verified by `PrStatusFixtureTest.test_merged_has_merge_fields` and reading `watch.md`
- [x] AC3: regression names each criterion with a follow-up title and body, verified by reading `watch.md` (no test covers this branch)
- [x] AC4: `unverified` with a reason, never `pass`, verified by `WatchMergedCaseTest.test_missing_post_merge_fails` and reading `watch.md`
- [x] AC5: closed unmerged ends `done (abandoned)` with no verify, verified by `WatchMergedCaseTest.test_abandoned_outcome_fails` and reading `watch.md`
- [x] AC6: `time_to_merge` from timestamps only, verified by `test_retro_metrics` (`test_watch_fields_loaded`, `test_watch_fields_missing_are_none`) and reading `watch.md` (the subtraction is not unit-tested)
- [x] AC7: After delivery section appended once, verified by `WatchMergedCaseTest.test_retro_without_section_fails` and `templates/retro.md`
- [x] AC8: report columns, aggregates, `--json` schema 2, `unknown` for missing values, verified by `test_retro_report` (`test_post_merge_columns_and_aggregates`, `test_json_document_shape`) and `test_retro_aggregate`
- [x] AC9: `sandbox-007` passes on a good synthetic run and fails on a bad one, verified by `WatchMergedCaseTest` and `evals.py check`
- [x] AC10: docs updated and roadmap item moved to Done, verified by reading the docs

## How to verify
```
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
python3 -m unittest discover -s tests -p test_evals.py -v
```

## Follow-ups
- `python3 -m unittest tests.test_retro_metrics tests.test_evals` fails with an `aicfg` import clash, because `scripts/evals.py` loads `scripts/aicfg.py` as a module. It also fails on `main`. Use the discover form above. Not fixed here.
- `Total min` now includes the wait for the PR to merge. The rollup's `STAGES` has no `watch` entry. Separate follow-up.
- No live `/spec-resume` on a real merged PR was run. The regression and `unverified` branches are checked by reading `watch.md`, not by a test.
- `watch.md` is 154 lines, above the ~140 line target in the plan.

Spec: `specs/081-watch-post-merge/spec.md` · Plan: `specs/081-watch-post-merge/plan.md`
Closes #81. Part of #77 (campaign gh:77, 4 of 4, after #<PREDECESSOR_PR>).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01BdiJDGmXUuJTx5qC4ADnaF
