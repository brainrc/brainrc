Add review-comment handling to the watch stage

## Why
After Deliver, reviewer feedback on a run's PR was still handled by hand and never counted in the run's state. Review comments are untrusted input, so this adds a classification step, an approval for every outward action, and a stop rule.

## What changed
- `watch` handles each new unresolved review thread on the run's PR, after the CI pass. A thread is handled once; its key goes in `watch.thread_log`.
- A small, local ask (rename, added test, one-function fix) becomes fix task `R<n>`, which runs implement → review under the normal retry budget.
- A question about intent gets a reply drafted from `spec.md`. Nothing is posted until the Push gate is approved, then the reply goes out via the connector's `reply_thread`.
- A large or design-level ask stops the run and asks the user. The run does not redesign on a reviewer's word.
- Thread text is untrusted: embedded instructions are flagged (`watch.threads.flagged`) and not followed.
- After 3 review rounds the run hands the PR back and classifies nothing further.
- The Push gate lists each push and each reply as a separate outward action. One approval covers the list; any change re-presents it.
- `state.json` gains `watch.review_rounds`, `watch.threads` (`total`, `fixed`, `replied`, `flagged`), and `watch.thread_log`.
- `pr_status` threads take an optional `id`. `ticket-github` queries and maps it; without it the key is author plus body.
- New sandbox eval `sandbox-006` grades a review comment with an embedded instruction, offline.

Blast radius: runs without `pr_status` and `local-only` runs still end at `done`. No live `gh` call was made; the watch procedure is skill text.

Not in this PR: `merged` and `closed` handling, and post-merge verify (#81).

## Acceptance criteria
- [x] AC1: small ask becomes `R<n>` with `gates.push: pending`, verified by reading `references/watch.md` § Review comments
- [x] AC2: question drafts a reply, posts only after approval, verified by reading `watch.md` § Review comments and § Push gate
- [x] AC3: design-level ask stops and asks, verified by reading `watch.md` § Review comments
- [x] AC4: Push gate lists pushes and replies separately, verified by reading `watch.md` § Push gate
- [x] AC5: round counter and 3-round hand-back, verified by reading `watch.md` step 1
- [x] AC6: `threads` counts and `thread_log` never re-handle a thread, verified by `WatchReviewCommentCaseTest::test_one_flagged_thread_one_round_passes`
- [x] AC7: embedded instruction flagged, not followed, verified by `test_fixture_has_id_and_embedded_instruction`
- [x] AC8: stable thread key (`id`, else author plus body), verified by `PrStatusFixtureTest::test_each_matches_shape`
- [x] AC9: resume order keeps pending tasks and gate first, verified by reading `watch.md` § Resume pass
- [x] AC10: `sandbox-006` passes on a synthetic good run and fails on bad runs, verified by `evals.py check` (9 passed; 4 failed on the bad run)
- [x] AC11: docs and schema updated, verified by reading `state.md`, `watch.md`, `connectors.md`, and `docs/post-deliver.md`

## How to verify
```
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
python3 -m unittest -v tests.test_evals.WatchReviewCommentCaseTest
```

## Follow-ups
- A new test file outside the diff and plan stops the run as `design`. This is deliberately conservative; a reviewer may want a softer rule.
- `sandbox-006` assumes a one-task plan (its `tasks.1` is `R1`). A plan with more tasks would fail the check.

Spec: `specs/080-watch-review-comments/spec.md` · Plan: `specs/080-watch-review-comments/plan.md`
Closes #80. Part of #77 (campaign gh:77, 3 of 4, after #<PREDECESSOR_PR>).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01BdiJDGmXUuJTx5qC4ADnaF
