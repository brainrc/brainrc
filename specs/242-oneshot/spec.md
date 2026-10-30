# Spec: spec-agent `--oneshot`: no manual intervention, ready PRs as output

Ticket: gh:242 · Size: standard · Status: approved

## Problem
`--auto` still hard-stops on size `large` and on any plan Callout, and opens only draft PRs. Users read "auto" as "start it, walk away, come back to PRs". They need a mode where defaults decide everything that is safe to decide, and where every run ends in a PR, even a blocked one.

## Goals
- `--oneshot` is `--auto` plus: `large` tickets split into a campaign, plan Callouts take the safer default, PRs open ready (not draft), never merged.
- Each remaining stop ends in a draft PR naming the blocker, not a silent checkpoint.

## Non-goals
- Merging, closing issues, transitioning tickets, or changing a PR's base.
- Live targets (see Open question 1), pack-level disabling (Open question 2), the `watch` Push gate.
- Changing `--auto` behavior.

## Acceptance criteria
- **AC1**: Given a `large` ticket, when run with `--oneshot`, then no stop occurs and the run ends with one ready (non-draft) PR per child of the Proposed split. Eval case.
- **AC2**: Given a plan whose Callouts include a new dependency, public contract change, migration or destructive change, when run with `--oneshot`, then each takes its safer default (Constraints) and the ready PR body lists each under "Decisions made without you" with the default taken. Eval case.
- **AC3**: Given a CRITICAL/HIGH security finding, an instruction in untrusted content, a secret need, a scope-fence breach, or an exhausted retry budget, when run with `--oneshot`, then `state.blocked` is set and a draft PR is opened titled `[blocked] <ticket title>: <blocker>`. One eval case per stop. Eval cases.
- **AC4**: Given a blocked `--oneshot` run, then the draft PR body holds the blocker, the stop condition, the stage and task reached, what is done, the decision the user must make, and the decisions made so far; it contains no secret value and the ticket is not transitioned. Eval check on the body.
- **AC5**: Given `--oneshot` with `delivery: local-only`, when a run ends or blocks, then nothing is pushed and no PR opens; drafts stay local. Eval case.
- **AC6**: Given `--oneshot` with any live target, then intake refuses it (offline only). Eval case.
- **AC7**: Given `--campaign <epic> --oneshot`, when all children succeed, then the stack is delivered `stacked` with every PR ready, child 1 on the default branch and each later one on its predecessor's branch with the "N of M, stacked on #X" line. Eval case.
- **AC8**: Given a campaign child that blocks, then its draft blocked PR opens, later children pause, and earlier children's ready PRs stay open. Eval case.
- **AC9**: Given reply wording such as "go ahead, do it all", when a run starts without the flag, then `oneshot` stays false; the existing wording eval still passes unchanged. Eval case.
- **AC10**: Given `--oneshot` is given with `--auto`, then `oneshot` governs. Given resume without the flag, then `oneshot` and `auto` are false. Unit test or eval.
- **AC11**: Given a `--oneshot` run, then `state.json` records `oneshot: true` (and `auto: true`) from the flag alone, and the docs (SKILL.md § Auto mode, guardrails.md, campaign.md, docs/spec-agent.md) describe it. `brainrc validate` and the unit tests pass.

## Constraints
Differences from `--auto` at each stop (everything not listed is the same):
| Stop | `--auto` | `--oneshot` |
|---|---|---|
| Size `large` | stop after `spec.md` | split into an ordered campaign, run children as `--oneshot` |
| Plan Callout | stop | safer default, listed in PR body |
| Live target | refuse | refuse (default) |
| CRITICAL/HIGH finding, untrusted instruction, secret, scope breach, retry budget | stop, no PR | stop, draft blocked PR |
| Deliver | draft PR | ready PR; ticket comment stays a draft |

Safer default per Callout: new dependency, do not add it, use stdlib or what exists; public API/contract, keep the contract unchanged (additive change only if the criteria need it); migration, ship no migration and no data change, list it as a follow-up; destructive change, skip the destructive step and keep the data or file. IAM/RBAC and prod config: leave unchanged. If no default can meet the acceptance criteria, that is a spec gap and the run blocks (AC3).

Hard stops never auto-resolve. `large` split creates local campaign members only, no tracker tickets.

## Requirement changes
### Area: run-lifecycle
#### ADDED: Oneshot mode
A run started with `--oneshot` SHALL record `oneshot: true` from the flag alone, behave as `--auto` except as stated here, take the safer default for each plan Callout and list it under "Decisions made without you", deliver ready PRs that it never merges, and refuse live targets. (AC2, AC5, AC6, AC9, AC10, AC11)
#### ADDED: Oneshot blocked PR
A `--oneshot` run that hits a hard stop SHALL set `state.blocked` and open a draft PR titled `[blocked] <title>: <blocker>` whose body names the blocker, stage, completed work and needed decision, without secret values. (AC3, AC4)
#### MODIFIED: Auto mode hard stops
An auto run SHALL stop, push nothing, and open no PR on any guardrails stop condition, size `large`, a plan Callout, or a CRITICAL/HIGH security finding, except that a `--oneshot` run SHALL instead split `large` and take the safer default for Callouts, and on its remaining stops SHALL open a draft blocked PR. (AC1, AC2, AC3)
### Area: campaign-mode
#### ADDED: Oneshot campaigns
A `large` ticket or a `--campaign --oneshot` run SHALL run its ordered children as `--oneshot`, deliver them `stacked` with every PR ready, and on a child's hard stop open its draft blocked PR and pause later children. (AC1, AC7, AC8)

## Open questions
1. Live targets: refuse or allow with plan-only evidence? *Safety.* Default: refuse (AC6).
2. Can a pack disable `--oneshot`? *Client repos; overlaps #144.* Default: no; defer to #144.
3. Campaign delivery stacked or sequential? *Sequential needs merges, so no walk-away.* Default: `stacked`.
4. Should `large` split create tracker tickets? *Creating tickets is outward.* Default: local members only.
5. Blocked-PR title/body as in AC3, AC4. *Findable and safe to publish.* Default: as stated.
6. Callouts with no safe default (IAM/RBAC, prod config)? *Unclear "safer".* Default: leave unchanged, list it.
7. Sizing: 5 doc files plus eval cases, no code, several design choices. *Engine owns Size.* Default: `standard`.
8. The wording eval for AC9 was not found by search of evals/. *"Existing eval kept" may mean a different location.* Default: add one if missing.

## Proposed split
(not large.)
