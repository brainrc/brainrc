# Verify: watch 2/4: `watch` stage for CI failures, with a Push gate

Run at 2026-10-21T14:51:03Z on commit `79fddb8` (branch `079-watch-ci-failures`, base `078-pr-status-connector`). Working tree clean at start.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests (full) | `python3 -m unittest discover -s tests` | pass: 328 run, 0 failed (`.runs/test.log`, exit 0) |
| Tests (targeted, verbose) | `python3 -m unittest -v tests.test_evals.WatchRedCiCaseTest tests.test_evals.CheckTest.test_state_numeric_index_segment` | pass: 7 run, 0 failed (`.runs/targeted.log`) |
| Lint | none configured (`state.commands.lint` = null) | not configured |
| Build | none configured (`state.commands.build` = null) | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: `OK: 26 skills, 9 agents, 0 commands` (`.runs/validate.log`, exit 0) |
| Eval, sandbox-005 on synthetic good run | `python3 scripts/evals.py check <synthetic-good> evals/cases/sandbox-005.toml` | pass: 6 passed, 0 failed (`.runs/evals-sandbox-005-good.log`, exit 0) |
| Eval, sandbox-005 on synthetic bad run | `python3 scripts/evals.py check <synthetic-bad> evals/cases/sandbox-005.toml` | expected fail: 3 passed, 3 failed, exit 1 (`.runs/evals-sandbox-005-bad.log`) |
| Plan / diff | n/a (offline only, no targets) | offline only |

Synthetic projects are git repos built in the session scratchpad (`main` with one commit, branch `001-demo`, `specs/001-demo/state.json` only). Their paths are in `.runs/synthetic-projects.txt`. Good state: `stage: watch`, one `own` entry with `task: C1`, `gates.push: pending`. Bad state: `cause: external`, no task, `gates.push: approved`.

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | Doc: `skills/spec-agent/references/watch.md:8-13` (Enter sets `stage: watch`, `watch.checked_at`, `head_sha`); `skills/spec-agent/SKILL.md:151` (Deliver step 3, enter `watch` per `watch.md` § Enter); `lifecycle.md:15` (`6b · watch` row). No executed run (see Notes). | pass |
| AC2 | Doc: `watch.md:14` (`local-only` or no `pr_status` goes to `done`, no `watch` key); `lifecycle.md:15` and `:81-82`. | pass |
| AC3 | Doc: `watch.md:24-41` (Resume pass: one `pr_status` read; `updated_at <= checked_at` and unchanged `head_sha` → "no change", nothing else touched; no loop). `state.md:149` (resume step 5 runs the pass). `skills/work/SKILL.md:13` (`/work` at `stage: watch`). | pass |
| AC4 | Doc: `watch.md:43-50` (step 1 writes `.runs/watch-<slug>-<sha7>.md`, summary only, raw log fenced as untrusted). Not executed; the sandbox-005 case has no `file` check on the summary (see Notes). | pass |
| AC5 | Doc: `watch.md:55-60` (external if red on base or no exact path match against `git diff <base>...HEAD --name-only`; one-line note; no task). Base-red count under the fixture treated as not red: `watch.md:21-22`. | pass |
| AC6 | Doc: `watch.md:61-66` (`cause: own`, `task: "C<n>"`, `tasks[]` entry with `review: each`, per-task loop, `attempts > 2` stops, +1 `metrics.post_deliver_retries` per creation/retry). Schema: `state.md:71-72`, `:101-102`. | pass |
| AC7 | Doc: `watch.md:68-76` (Push gate: `gates.push: pending` per push, gate shows diff stat, `git log --oneline`, failing check, `gates.push_sha`; push only on approval; rejection keeps commits local). Guardrail: `guardrails.md:45`. Approval-reply rule: `SKILL.md` § gates (the Push gate sentence). Gate shape: `lifecycle.md:88` (`## Gate presentation`). | pass |
| AC8 | `state.md:71-72` (`watch` schema), `:99` (`stage` includes `watch`), `:100` (`gates.push`), `:101` (`watch` fields), `:102` (`metrics.post_deliver_retries`), `:103` (`metrics.gates.push`, `gate_rework.push`). `lifecycle.md:15, :81-82`. `docs/post-deliver.md:3-4` (status line: CI failures and Push gate built), `:101-104` (build order item 3 done). `docs/spec-agent.md:20-28` (watch stage summary). | pass |
| AC9 | `tests/test_evals.py` `WatchRedCiCaseTest` (5 tests incl. `test_own_failure_with_pending_push_passes`, `test_external_cause_fails`, `test_approved_push_gate_fails`, `test_second_ci_failure_entry_fails`) — all pass in `.runs/targeted.log`. CLI path: `scripts/evals.py check` on synthetic good run exits 0 (`.runs/evals-sandbox-005-good.log`), on synthetic bad run exits 1 with the three expected FAILs (`.runs/evals-sandbox-005-bad.log`). Case: `evals/cases/sandbox-005.toml:1-33`. Fixture path itself (`SPEC_PR_STATUS_FIXTURE`) is prose only, not executed (Q6). | pass |
| AC10 | `python3 scripts/aicfg.py validate` exit 0 (`.runs/validate.log`); full suite 328 OK (`.runs/test.log`); numeric index pass and fail: `tests/test_evals.py` `CheckTest.test_state_numeric_index_segment` (index 0 passes; index 1 and -1 fail with `= None`), and `test_present_false_passes_when_absent_and_fails_when_set`. Dotted-index code: `scripts/evals.py:_field`. | pass |

## Notes
- No test or check ran `watch.md` as an agent would; the `watch` stage is a skill procedure. AC1–AC8 are verified by reading the cited lines, not by execution. Per resolved Open question 6, AC9 is verified on a synthetic run folder, not a nested sandbox run.
- AC9 grading: the `SPEC_PR_STATUS_FIXTURE` read is not exercised by any check. The eval checks state only, plus `main_untouched`. No PR-creation check exists in `sandbox-005.toml` (the spec's "no PR created by the grader" is not separately graded).
- The plan's T6 case list included `file {spec}/.runs/watch-unit-tests-3f2a9c1.md matches test_greet\.py`. `sandbox-005.toml` omits it, so the summary file's content is not graded. AC9's four conditions do not require it. Non-blocking; flagged for #80/#81 or a follow-up.
- AC4 wording ("summary... saved under `.runs/`") is met by the procedure text, but `watch.md:50` ("The raw log stays in `.runs/`") leaves unclear whether the raw log is persisted. Non-blocking wording note.
- Flakes: none. No test re-run. Skipped: lint and build (not configured). No network, no `gh` used.
- Nothing committed.
