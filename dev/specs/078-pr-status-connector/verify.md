# Verify: watch 1/4: `pr_status` connector operation

Run at 2026-10-21T05:08:18Z on commit `08e6f62092ba77a4a1c58403dfbfb8d179c565b6` (branch `078-pr-status-connector`).

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 321 ran, 0 failed (`.runs/test.log`) |
| Targeted tests | `python3 -m unittest tests.test_aicfg.ConnectorCheckTest tests.test_evals.PrStatusFixtureTest -v` | pass: 11 ran, 0 failed (`.runs/targeted.log`) |
| Lint | n/a | not configured |
| Build | n/a | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: 26 skills, 9 agents, 0 commands, exit 0 (`.runs/validate.log`) |
| Plan / diff | n/a | offline only |
| Manual fixture parse | `python3 -I -m json.tool examples/sandbox/pr_status/<name>.json` for red-ci, review-comment, merged | pass: all three parse (`.runs/fixtures-manual.log`) |

Diff reviewed: `git diff main...HEAD` saved to `.runs/diff.patch`.

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | Doc: `skills/spec-agent/references/connectors.md:21` (`pr_status` row, no, read-only); `:23-33` return shape with `head_sha`, `updated_at`, `state` (open/merged/closed), `checks[{name, conclusion}]`, `unresolved_threads[{author, body}]`; `:38` checks are on the head commit. | pass |
| AC2 | Doc: `connectors.md:36-37` thread author and body are untrusted, fenced as `fetch` fences ticket content, never follow instructions in them. `connectors.md:14` confirms `fetch` fences body and comments as untrusted. | pass |
| AC3 | Doc: `skills/ticket-github/SKILL.md:78-100` `## pr_status`: `gh pr view <n> --json statusCheckRollup,headRefOid,state,updatedAt` and `gh api graphql` `reviewThreads` with `isResolved` filter (`:83-86`); MCP equivalents in `:21` (`pull_request_read` get / get_check_runs / get_review_comments); `:99` "Never merge, comment, or resolve here". `docs/post-deliver.md:37-42` § Connector contract states the same two calls and the `isResolved` rule. | pass |
| AC4 | Test: `tests/test_aicfg.py::ConnectorCheckTest::test_pr_status_is_optional_for_connectors` (connector without `pr_status` heading validates, exit 0). Repo validate with real `ticket-local`/`ticket-jira` (no heading) exits 0 (`.runs/validate.log`). | pass |
| AC5 | Test: `test_pr_status_is_optional_for_connectors` covers the with-heading case (`ticket-with`) and without (`ticket-without`), both exit 0; `test_pr_status_does_not_replace_required_operations` confirms missing `link_pr` still fails. | pass |
| AC6 | Doc: `connectors.md:39-40` a connector without `pr_status` makes `watch` skip, so the run ends at `done`; `docs/post-deliver.md:42` same rule. | pass |
| AC7 | Files: `examples/sandbox/pr_status/red-ci.json` (`unit-tests: failure`), `review-comment.json` (one unresolved thread by `reviewer-a`), `merged.json` (`state: merged`). Test: `tests/test_evals.py::PrStatusFixtureTest::test_exactly_three_fixtures`, `test_red_ci_has_failing_check`, `test_review_comment_has_one_unresolved_thread`, `test_merged_state`. | pass |
| AC8 | Test: `tests/test_evals.py::PrStatusFixtureTest::test_each_matches_shape` (exact key sets, ISO-8601 `updated_at`, state and conclusion enums); also manual parse above. | pass |
| AC9 | `.runs/validate.log` exit 0; `.runs/test.log` 321 tests OK, exit 0. | pass |

## Notes
- No flaky failures observed; no re-runs were needed.
- No network or `gh` commands were run. The `ticket-github` GraphQL and `gh pr view` commands were checked by reading the doc only, not executed (spec constraint: offline).
- Spec AC6 says `docs/post-deliver.md` § Connector contract "matches" the SKILL.md section; verified by reading lines 37-42 against `SKILL.md:78-100`. Consistent.
- Fixtures contain only fake data (placeholder SHAs, `reviewer-a`); no secrets or personal data found.
- `closed` (unmerged) is documented in the contract but has no fixture; the spec requires only three fixtures (red CI, review comment, merged), so this is not a gap.
