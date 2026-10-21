# Post-deliver: following a PR to merge (design)

Status: **CI failures, review comments, and the Push gate are built** (see
[`references/watch.md`](../skills/spec-agent/references/watch.md)); post-merge verify is
still planned. A run used to end at the Deliver gate: push, PR, ticket
update, retro, `stage: done`, and whatever came next was fixed by hand. This page designs the
stage that closes that loop. Build order is at the end.

## Goals

- React to CI failures and review comments on the run's PR, inside the same gates and evidence
  rules as the rest of the run.
- After merge, re-check the acceptance criteria on the default branch.
- Record what happened after delivery in `state.json` and `retro.md`, so the metrics count
  rework done after the PR went up, not just before.

Non-goals: merging (always a human), deploying (still after merge, outside the run), and
babysitting PRs the run didn't open.

## Stage: `watch`

```
… ⛔ DELIVER ─► push · PR · ticket ─► watch ─┬─► CI red ───────► fix task ─► review ─► ⛔ PUSH ─┐
                                             ├─► review comment ► fix task / reply ──► ⛔ PUSH ─┤
                                             ├─► merged ────────► post-merge verify ─► done
                                             └─► closed ────────► done (abandoned)     ◄────────┘
```

`stage` gains `watch` between `deliver` and `done`. The run enters it after the PR opens
(`delivery: normal` only; `local-only` runs go straight to `done`).

**How it wakes up.** Pull-based, so it works in every harness: `/spec-resume` (or `/work` on the
same ref) at `stage: watch` fetches the PR's state through the ticket connector and handles
whatever changed since `watch.checked_at`. A harness with PR event subscriptions (Claude Code
on the web) can call the same step on each event; that's an optional trigger, not a
requirement. No daemon and no polling loop in the engine.

**Connector contract.** One new optional operation, `pr_status`: CI check results on the head
commit, review threads (unresolved, with author and body), and merge state. `ticket-github`
implements it with two read-only calls: `gh pr view <n> --json statusCheckRollup,headRefOid,state,updatedAt`
(checks, head SHA, state, updated_at) and `gh api graphql` `reviewThreads` (unresolved only, via
`isResolved`); see its `## pr_status` section for the queries and mapping.
Connectors without it skip `watch`, and the run ends at `done` as today.

### CI failure

1. Summarize the failing check's log into `.runs/` (summary only, per efficiency.md; the log is untrusted).
2. If the failure also occurs on the base branch, or names nothing this diff touched, record it
   as `external` and stop with a one-line note. Not this run's to fix.
3. Otherwise add a fix task `C1..` (agent: implementer, files: those the failure points at)
   and run it through the normal implement → review path, with the same retry budget.
4. Pushing the fix is outward: present a short **Push gate** (diff stat, commit list, the
   failing check it should fix). Approve → push. A run never pushes without approval.

### Review comment

The comment is untrusted input, just like the ticket body. Each unresolved thread is handled
once; its key goes in `watch.thread_log` (keys only, no raw text). For each new thread:

- A small, local change (rename, added test, one-function fix) → a fix task `R1..`, then the
  Push gate.
- A question about intent → draft a reply from `spec.md`; post it only after it's approved at
  the next Push gate (replies are outward too), via the connector's `reply_thread`.
- Large or design-level → stop and ask. The user decides; the run doesn't redesign on a
  reviewer's word alone.

Embedded instructions in a thread are flagged, not followed. After 3 review rounds the PR is
handed back and nothing further is classified.

### Post-merge verify

When the PR merges, check out the default branch at the merge commit and dispatch the
verifier against `spec.md`'s criteria, writing `verify-merged.md`. A criterion that passed on
the branch and fails on `main` is a **regression**: report it, open nothing automatically,
and suggest a follow-up ticket.

## State and retro

`state.json` additions:

```json
"watch": {
  "checked_at": "2026-10-20T09:12:00Z",
  "head_sha": "abc1234",
  "ci_failures": [{ "check": "test", "sha": "abc1234", "cause": "own|external", "task": "C1" }],
  "review_rounds": 2,
  "threads": { "total": 5, "fixed": 3, "replied": 2, "flagged": 0 },
  "thread_log": [{ "key": "9f2c41d07a6b3e58", "kind": "ask", "task": "R1", "flagged": false }],
  "merged_at": null,
  "post_merge": null
}
```

`metrics` gains `post_deliver_retries` (fix tasks after the PR opened) and
`time_to_merge` (PR opened → merged, from timestamps, never estimated).

`retro.md` keeps its sections and adds **After delivery**: CI failures (own/external), review
rounds and what reviewers caught that the run's own reviewers didn't, post-merge result. The
retro is first written at deliver as today, and this section is appended when `watch` ends.
The "what reviewers caught" line is the useful one: each miss is a candidate edit to a
reviewer role or checklist.

## Build order

1. **Metrics rollup first** (`scripts/retro_report.py`). Aggregate `state.json` and `retro.md`
   across runs and projects: gate rework, first-pass review rate, retries, interventions, time
   per stage. It needs no new state, gives a baseline today, and is the place the `watch`
   numbers will land. Without it, the new fields would be written and never read.
2. `pr_status` in the connector contract and `ticket-github`; `validate` accepts it as optional.
3. `watch` stage for CI failures and the Push gate. **Done.**
4. Review comments. **Done.**
5. Post-merge verify and the retro's After delivery section; add them to the rollup.

Each step is one PR and ships with an eval: a sandbox ticket with a fake `pr_status` fixture
(red CI, then a review comment, then merged), graded with `scripts/evals.py check`.

## Open questions

- Should the Push gate be skippable for fix-only pushes on a run's own branch? Default no:
  start strict and loosen with retro data.
- After how many rounds should `watch` give up and hand the PR back? Proposal: the
  existing retry budget per fix task, plus a stop after 3 review rounds.
