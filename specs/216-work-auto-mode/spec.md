# Spec: spec-agent `--auto` mode, no gate stops, draft PR(s) as output

Ticket: gh:216 · Size: standard · Status: approved

## Problem
Every `/work` run stops at the Spec, Plan, and Deliver gates. A campaign also adds a Campaign gate and
a Spec and Plan gate per child: gh:92 needed 13 replies, gh:93 needed 12 plus two review-context
questions. A user with well-specified tickets wants to start a run, walk away, and review a draft PR.
Today the engine forbids that on purpose. Earlier wording never approves a later gate, after an
E2E run self-approved a gate it hadn't presented (docs/e2e-runs.md). Auto mode must be an explicit,
recorded opt-in that wording can't switch on, and it must keep every hard stop.

## Goals
- `/work <ref> --auto` runs to a draft PR with no gate stops, and records each gate as auto-approved.
- `/work --campaign <ref> --auto` does the same per child: stacked draft PRs.
- Every hard stop still stops, opens no PR, and leaves the branch unpushed.

## Non-goals
- Merging, retargeting a base, or closing issues (never automatic).
- Auto mode for `watch` and its Push gate (fix pushes after review stay gated).
- Changing gates for runs started without `--auto`.

## Acceptance criteria
- **AC1**: Given `/work <ref> --auto`, then intake records `auto: true` in `state.json`, set from the flag only. Given a run started without it, no reply wording sets it (the existing self-approval eval still passes).
- **AC2**: Given an auto run of a `small` and of a `standard` ticket, then it ends with a draft PR and no stop. `log.md` has each gate's summary marked `auto-approved`, and `metrics.gates.<gate>` has both timestamps.
- **AC3**: Given an auto run, then its PR body lists the spec, plan, and verify paths, plus a "Decisions made without you" section with every open question the analyst answered by its stated default.
- **AC4**: Given an auto run that hits a guardrails stop condition (attempts > 2, scope breach, spec gap, untrusted-content instruction, secrets), size `large`, or a plan Callout (new dependency, public API or contract change, migration, IAM/RBAC, prod config, destructive infra), or a CRITICAL/HIGH security finding, then it checkpoints, sets `state.blocked`, pushes nothing, opens no PR, and reports why.
- **AC5**: Given an auto run, then targets are offline-only. Naming a live target with `--auto` is refused at intake.
- **AC6**: Given a blocked auto run, when `/spec-resume` runs, then gates are normal from there unless `--auto` is given again.
- **AC7**: Given `/work --campaign <ref> --auto --shape ordered`, then the Campaign gate and each child's Spec and Plan gates are auto-approved, and the run ends with stacked draft PRs, one per child, in dependency order. A child's hard stop pauses the later children (existing Failure rule) and opens no PR for it or them.
- **AC8**: Each AC4 hard stop has an eval case (sandbox ticket + case file) showing the run stopped with no PR.

## Constraints
- Harness-neutral skill text. Rules files stay short (they load every session).
- Evals stay offline (local sandbox, PR status fixtures), stdlib only.

## Requirement changes

### Area: run-lifecycle
#### ADDED: Auto mode
A run started with `--auto` SHALL record `auto: true` from the flag alone, pass every gate without
stopping while logging each as `auto-approved` with timestamps, and deliver a draft PR whose body
lists the decisions made without the user. (AC1, AC2, AC3, AC5, AC6)
#### ADDED: Auto mode hard stops
An auto run SHALL stop, push nothing, and open no PR on any guardrails stop condition, size `large`,
a plan Callout, or a CRITICAL/HIGH security finding. (AC4, AC8)

### Area: campaign-mode
#### ADDED: Auto campaigns
An ordered campaign started with `--auto` SHALL auto-approve its Campaign gate and each child's Spec
and Plan gates, and deliver stacked draft PRs in dependency order. A child's hard stop SHALL pause
the later children. (AC7)

## Open questions
All five resolved at the Spec gate with their defaults.
1. Ticket comments in auto mode: post them with the PR, or keep them as drafts listed in the PR body? *Posting reaches the ticket's watchers before anyone reviews.* Default: drafts only. `ticket-comment.md` is written and linked from the PR body, and the user posts it.
2. `--auto` authorizes `git push` and a **draft** PR without a Deliver gate. That is a new exception to guardrails § Outward actions. Is that the intent? *It's the one outward action the whole feature needs.* Default: yes, draft only, and only for the run's own branch.
3. In fallback mode, a standard run asks whether to stop for a fresh-session review. Under `--auto`: continue shared, recorded as `review_context: shared`? Default: yes.
4. Flag name in state: `auto` (the ticket's `mode_auto` is a placeholder)? `mode` already means inline/subagent/fallback. Default: `auto`.
5. A security trigger with no CRITICAL/HIGH finding: continue (ticket) or stop? Default: continue, listed in "Decisions made without you".

## Proposed split
Not taken: resized to `standard` at the Spec gate and built as one run. The slices below became the plan's task order.
1. **Auto mode for single runs** (AC1-AC6): flag and state, gate logging, hard stops, PR body section, resume. Files: `skills/work/SKILL.md`, `skills/spec-agent/SKILL.md`, `references/guardrails.md`, `references/lifecycle.md`, `references/state.md`, `templates/pr-body.md`, docs/spec-agent.md.
2. **Eval cases for auto runs** (AC2 and AC8 graded): sandbox tickets per hard stop, case files, any new `evals.py` check kind (e.g. a `log` gate marker, "no PR/branch pushed"), tests. Files: `examples/sandbox/tickets/`, `evals/cases/`, `scripts/evals.py`, `tests/test_evals.py`, docs/evals.md. After 1.
3. **Auto campaigns** (AC7): `references/campaign.md` (Campaign gate, per-child gates, stacked delivery under `--auto`), a campaign eval case. After 1 and 2.
