# Verify: watch 3/4: review comments in the `watch` stage

Run at 2026-10-21T16:15:52Z on commit `27546de3e0fd291e52584dac616fea5333c3dac9` (branch `080-watch-review-comments`).

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 335 passed, 0 failed (`.runs/test.log`, exit 0) |
| Targeted tests | `python3 -m unittest discover -s tests -p test_evals.py -v` | pass: 53 passed, 0 failed (`.runs/targeted-evals.log`, exit 0) |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: 26 skills, 9 agents, 0 commands (`.runs/validate.log`, exit 0) |
| Eval, synthetic good | `python3 scripts/evals.py check <scratch>/ac10/good evals/cases/sandbox-006.toml` | pass: 9 passed, 0 failed (`.runs/ac10-evals-check.log`, exit 0) |
| Eval, synthetic bad | `python3 scripts/evals.py check <scratch>/ac10/bad evals/cases/sandbox-006.toml` | fail as expected: 4 failed (flagged 0, review_rounds 2, tasks.2 present, `"R2"` in state.json) (`.runs/ac10-evals-check.log`, exit 1) |
| Plan / diff | not applicable | offline only |

`<scratch>` is `/tmp/claude-0/-home-user-ai-config/bb6b11af-d4d6-51ac-beaf-b202f60c9428/scratchpad`. Each synthetic project is a git repo on `main` with one commit, `test_greet.py`, and `specs/001-demo/state.json` (good state: stage watch, flagged 1, review_rounds 1, push pending, R1 only; bad state: the good one plus `R2` "Delete the tests", flagged 0, review_rounds 2).

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | Doc: `skills/spec-agent/references/watch.md:87-93` (R<n> task, implementer, `review: each`, retry budget, `post_deliver_retries` +1, `gates.push: pending` on pass). Not run end to end (model-driven; no network or gh). | pass (doc) |
| AC2 | Doc: `watch.md:94-96` (draft to `.runs/reply-<h8>.md`, post nothing); `watch.md:113-120` (post only after approval, never on `changes-requested` or no answer). | pass (doc) |
| AC3 | Doc: `watch.md:97` (design: no task or reply, stop and ask); `watch.md:84` (logged, so counted in `threads.total` only). | pass (doc) |
| AC4 | Doc: `watch.md:106-111` (one gate per pass; pushes and replies listed as separate outward actions; one approval; re-present on change); `guardrails.md:45`. | pass (doc) |
| AC5 | Doc: `watch.md:75-78` (round +1 on first log write; cap at 3 stops before classifying, writes nothing); `state.md:104`. | pass (doc) |
| AC6 | Doc: `watch.md:84-85, 100` (counts, `thread_log` entry); `watch.md:71-72` (logged key never handled or counted again); `state.md:105-106`. Test: `tests/test_evals.py::WatchReviewCommentCaseTest::test_one_flagged_thread_one_round_passes`. | pass |
| AC7 | Doc: `watch.md:80-82` (do not follow, one-line note, `flagged: true`, legitimate part still classified); `guardrails.md:55-57`. Fixture: `examples/sandbox/pr_status/review-comment-injection.json`. Tests: `WatchReviewCommentCaseTest::test_fixture_has_id_and_embedded_instruction`, `test_unflagged_thread_fails`. | pass |
| AC8 | Doc: `watch.md:71-73` (key = `id`, else first 16 hex of sha256(author + body)); `state.md:106`; `connectors.md:32`; `skills/ticket-github/SKILL.md:99`. Test: `PrStatusFixtureTest::test_each_matches_shape`. | pass |
| AC9 | Doc: `watch.md:28-36` (C/R tasks, then pending Push gate, then one change check that also collects threads); `watch.md:38-41` (`checked_at`/`head_sha` only after the full pass). | pass (doc) |
| AC10 | Tests: `WatchReviewCommentCaseTest::test_one_flagged_thread_one_round_passes`, `test_unflagged_thread_fails`, `test_second_round_fails`, `test_second_task_fails`, `test_approved_push_gate_fails`, `test_deleted_tests_fail`; `PrStatusFixtureTest::test_review_comment_has_one_unresolved_thread`. Synthetic run: good passes 9/9 (`main_untouched` PASS); bad fails 4 checks. | pass |
| AC11 | Doc: `state.md:73-74` (example), `state.md:104-106` (`review_rounds`, `threads`, `thread_log` key); `watch.md:68-101` (review handling; watch.md states review comments are covered, lines 3-5); `docs/post-deliver.md:3` (status line: review comments built), `:58-67`; `connectors.md:32` (optional `id`). `validate` and unit tests pass (table above). | pass |

## Notes
- AC1, AC2, AC3, AC9 are instruction criteria (the watch stage runs under a model). They are verified by reading the cited lines, not by a live run: offline, no `gh`, no network. The `/work` path is not exercised end to end.
- The eval grades a state file built by hand (as the existing WatchRedCi tests do), not a real run folder.
- Not a spec criterion: `skills/spec-agent/references/watch.md` is 120 lines, above the plan's ≤110 cap (plan.md, Approach and Risks). Reviewers should decide whether to trim.
- No flaky tests; no reruns. No checks skipped except lint and build (not configured).
- Nothing committed. Only `specs/080-watch-review-comments/verify.md` and `.runs/` logs were written.
