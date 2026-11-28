Add optional pr_status connector operation to read PR state

## Why
After Deliver, red CI, review comments, and merges are handled by hand. The planned `watch` stage needs to read PR state through the ticket connector, and no connector operation does yet. This adds that read-only operation, its GitHub implementation, and offline fixtures for later evals.

## What changed
- The connector contract (`skills/spec-agent/references/connectors.md`) documents `pr_status` as optional and read-only, with its return shape. Thread author and body are untrusted and fenced like `fetch` content. A connector without it makes `watch` skip, so the run ends at `done`.
- `ticket-github` implements `pr_status` with `gh pr view --json` for checks, head sha, state, and updated_at, plus one GraphQL call for unresolved review threads. It writes nothing. The GitHub MCP equivalents are listed.
- `docs/post-deliver.md` matches the `ticket-github` section. `docs/spec-agent.md` lists `pr_status` as optional.
- Sandbox fixtures in `examples/sandbox/pr_status/` cover red CI, one unresolved review comment, and merged.
- `aicfg validate` tests cover connectors with and without `pr_status`. No validate code changed.

Not in this PR: the `watch` stage, the Push gate, fix tasks, and the `state.json` watch fields (#79 to #81).

## Acceptance criteria
- [x] AC1: `pr_status` row and return shape in `connectors.md`, verified by reading the doc
- [x] AC2: thread text marked untrusted in `connectors.md`, verified by reading the doc
- [x] AC3: `## pr_status` in `ticket-github/SKILL.md`, matching `post-deliver.md`, verified by reading both
- [x] AC4: connector without the heading passes validate, verified by `ConnectorCheckTest::test_pr_status_is_optional_for_connectors`
- [x] AC5: with and without the heading both pass, and a missing `link_pr` still fails, verified by `ConnectorCheckTest`
- [x] AC6: skip rule stated in `connectors.md` and `post-deliver.md`, verified by reading both
- [x] AC7: three fixture files, one per state, verified by `PrStatusFixtureTest`
- [x] AC8: fixtures match the shape offline, verified by `PrStatusFixtureTest::test_each_matches_shape`
- [x] AC9: `aicfg validate` exits 0 and the 321 unit tests pass

## How to verify
```
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
python3 -m unittest tests.test_aicfg.ConnectorCheckTest tests.test_evals.PrStatusFixtureTest -v
```

The `gh` and GraphQL calls were checked by reading only, since this change runs offline. Run `pr_status` against a real PR before relying on it.

## Follow-ups
- The test enum lists are copied from `connectors.md`, not generated from it (LOW, not addressed).
- `closed` (unmerged) is in the contract but has no fixture. The spec did not require one.
- The `gh` and GraphQL calls have not been run live (see above).

Spec: `specs/078-pr-status-connector/spec.md` · Plan: `specs/078-pr-status-connector/plan.md`
Closes #78. Part of #77 (campaign gh:77, 1 of 4).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01BdiJDGmXUuJTx5qC4ADnaF
