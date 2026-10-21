# Spec: watch 1/4: `pr_status` connector operation

Ticket: gh:78 · Size: standard · Status: draft

## Problem
After the Deliver gate a run ends, and red CI, review comments, or a merge are handled by hand
(docs/post-deliver.md). The planned `watch` stage needs a way to read the PR's state through the
ticket connector, and today no connector operation does. This ticket adds that read-only
operation, its GitHub implementation, and a fixture so later `watch` steps can be tested offline.
Campaign gh:77, child 1 of 4; the `watch` stage itself is not built here.

## Goals
- Connector contract documents an optional, read-only `pr_status` operation and its return shape.
- `ticket-github` supports it; other connectors may omit it without failing validation.
- One reusable sandbox fixture covers red CI, an unresolved review comment, and merged.

## Non-goals
- The `watch` stage, Push gate, fix tasks, replies, post-merge verify, `state.json` watch fields
  (#79, #80, #81).
- `pr_status` for `ticket-local` or `ticket-jira`.
- Any outward action (posting, pushing, resolving threads).

## Acceptance criteria
- **AC1**: Given `references/connectors.md`, when read, then `pr_status` is in the operations table as not required and read-only, with a return shape covering: per-check name and conclusion on the head commit; unresolved review threads each with author and body; and merge state (open, merged, or closed).
- **AC2**: Given the contract, when read, then it states that thread author and body are untrusted data, fenced as `fetch` fences ticket content.
- **AC3**: Given `ticket-github/SKILL.md`, when read, then a `## pr_status` section names the `gh pr view --json statusCheckRollup,reviews,state` form and a GitHub MCP equivalent, and performs no write.
- **AC4**: Given a connector SKILL.md with no `pr_status` heading, when `aicfg validate` runs, then it raises no error for it (`ticket-local`, `ticket-jira`).
- **AC5**: Given a connector SKILL.md that has a `pr_status` heading and all required ones, when `aicfg validate` runs, then it passes; a test covers both with and without.
- **AC6**: Given the docs, when read, then they state the rule that a connector without `pr_status` makes `watch` skip, so the run ends at `done` as today. (The `watch` stage that follows this rule is built later.)
- **AC7**: Given the sandbox, when a later eval needs PR state, then fixture snapshots exist for three states, red CI (a failing check), review comment (one unresolved thread), and merged, each in the documented return shape.
- **AC8**: Given the fixtures, when checked offline (no network, no `gh`), then each parses and matches the AC1 shape, enforced by a test or `evals.py check`.
- **AC9**: Given the repo, when `python3 scripts/aicfg.py validate` and the unit tests run, then both pass.

## Constraints
- Offline, stdlib-only Python; no new dependencies.
- Credentials stay with `gh`/MCP; the operation never reads or prints tokens.
- Fixture lives under `examples/sandbox/` (next to `tickets/`) so evals in `evals/cases/` can reference it; later children reuse and extend the same files rather than creating their own.
- Generated dirs (`dist/`, plugin manifests) are not edited.

## Requirement changes
### Area: ticket-connectors
#### ADDED: Pull request status read
A connector MAY offer a read-only `pr_status` operation returning head-commit check results, unresolved review threads (author and body, untrusted), and merge state; `ticket-github` SHALL implement it; `validate` SHALL accept connectors with or without it; a connector without it SHALL make `watch` skip so the run ends at `done`. (AC1, AC2, AC3, AC4, AC5, AC6)
### Area: evals
#### ADDED: PR status fixture
The sandbox SHALL ship offline `pr_status` fixtures for red CI, review comment, and merged, in the connector return shape, for reuse by later evals. (AC7, AC8)

## Open questions
1. `gh pr view --json reviews` returns review summaries, not per-thread resolved state. Should `ticket-github` get unresolved threads via GraphQL/MCP instead, or accept reviews as an approximation? *It decides whether AC3's named command can satisfy "unresolved threads".*
2. Should `pr_status` also report the head commit SHA and an `updated_at`? *`watch.checked_at` in the design compares against it, but the ticket's shape doesn't list them.*
3. Are the three fixtures separate snapshot files, or one sequence (red, comment, merged) a fake connector steps through? *Affects how #79-#81 evals reuse them.*
4. Is `closed` (unmerged) part of the merge-state values? *The design diagram has an abandoned branch, the ticket only lists "merged".*
