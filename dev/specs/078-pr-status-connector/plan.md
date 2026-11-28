# Plan: watch 1/4: `pr_status` connector operation

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** connector contract gains optional `pr_status` (additive; existing and pack connectors unaffected)
- **Migrations / data changes:** none
- **Security triggers touched:** untrusted input (review thread author/body), documented only; no code path executes it
- **Domains:** scripting
- **Environments affected on deploy:** none (docs, tests, fixtures)
- **Destructive or replacing changes:** none

## Approach
Docs carry the contract. `skills/spec-agent/references/connectors.md` gets a `pr_status` row (required: no, kind: read-only, allowed: after link_pr), a return-shape block, the untrusted-fencing rule (same as `fetch`), and the rule that a connector without `pr_status` makes `watch` skip, so the run ends at `done`. The shape, fixed here so wave-1 tasks agree:
`{"head_sha": str, "updated_at": ISO-8601 str, "state": "open"|"merged"|"closed", "checks": [{"name": str, "conclusion": "success"|"failure"|"neutral"|"cancelled"|"skipped"|"timed_out"|"action_required"|"pending"}], "unresolved_threads": [{"author": str, "body": str}]}`.

`aicfg/validate.py` `check_connectors` already only enforces `config.REQUIRED_CONNECTOR_OPS` (`fetch, comment, transition, link_pr`), so `pr_status` is optional already. No code change: we pin the behavior with tests in `ConnectorCheckTest` (reusing `write_skill`, `quiet`, `TempRepoCase`). Adding `pr_status` to a required tuple was rejected because it would break `ticket-local`, `ticket-jira`, and pack connectors.

Fixtures are three JSON files under `examples/sandbox/pr_status/`. A new test class in `tests/test_evals.py` checks them offline against the shape with a small stdlib checker in the test (no `evals.py` change; #79 can promote it to a check kind if an eval needs it).

## Files
| File | Change |
|---|---|
| `skills/spec-agent/references/connectors.md` | modify: `pr_status` row, shape, untrusted rule, skip rule |
| `skills/ticket-github/SKILL.md` | modify: intro list, table row, `## pr_status` section |
| `docs/post-deliver.md` | modify: § Connector contract command matches SKILL.md |
| `tests/test_aicfg.py` | modify: `ConnectorCheckTest` with/without `pr_status` |
| `examples/sandbox/pr_status/{red-ci,review-comment,merged}.json` | new: fixtures |
| `examples/sandbox/README.md` | modify: one line pointing at fixtures |
| `tests/test_evals.py` | modify: `PrStatusFixtureTest` |
| `changelog.d/078-pr-status-connector.md` | new: `bump: patch` |

## Risks
- Shape drift between contract, SKILL.md, and fixtures, mitigated by fixing the shape in this plan and one batch review across all tasks.
- `statusCheckRollup` mixes CheckRun (`name`, `conclusion`) and StatusContext (`context`, `state`) items, mitigated by T2 documenting the mapping to `name`/`conclusion`.
- Fixture under the sandbox breaks `SandboxSetupTest`, mitigated by committing JSON only (no `.env`-like or ignored names).

## Test strategy
AC4/AC5: unit tests in `tests/test_aicfg.py::ConnectorCheckTest`. AC7/AC8: `tests/test_evals.py::PrStatusFixtureTest` (parse, keys, types, enums, one per state: a `failure` check; exactly one thread; `state: merged`). AC1–AC3, AC6: read in review. AC9: full validate + unit tests after each task.

## Tasks
- [ ] **T1** [agent: implementer] Contract: `pr_status` in connectors.md + changelog fragment
  - files: `skills/spec-agent/references/connectors.md`, `changelog.d/078-pr-status-connector.md`
  - criteria: AC1, AC2, AC6, AC9
  - review: each
  - wave: 1
- [ ] **T2** [agent: implementer] `ticket-github` `## pr_status` (gh + GraphQL + MCP, read-only); align post-deliver.md
  - files: `skills/ticket-github/SKILL.md`, `docs/post-deliver.md`
  - criteria: AC3, AC6, AC9
  - review: each
  - wave: 1
- [ ] **T3** [agent: implementer] Validate tests: connectors with and without `pr_status`
  - files: `tests/test_aicfg.py`
  - criteria: AC4, AC5, AC9
  - review: batch
  - wave: 1
- [ ] **T4** [agent: implementer] Sandbox fixtures + offline shape test
  - files: `examples/sandbox/pr_status/red-ci.json`, `examples/sandbox/pr_status/review-comment.json`, `examples/sandbox/pr_status/merged.json`, `examples/sandbox/README.md`, `tests/test_evals.py`
  - criteria: AC7, AC8, AC9
  - review: batch
  - wave: 1
