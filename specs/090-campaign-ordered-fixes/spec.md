# Spec: Campaign ordered-shape fixes from gh:77

Ticket: gh:90 · Size: standard · Status: approved

## Problem
The first ordered campaign (gh:77) shipped, but its children's stacked PRs merged into their stacked bases instead of `main`, so three children only reached `main` through an extra PR. The run also hit gaps the procedure doesn't cover: no member status for "verified, awaiting Deliver", no documented stacked delivery, campaign state scattered across child branches, same-wave tasks linking each other's new files, implementers writing outside their worktree, and engine edits to approved artifacts with no rule. Each gap cost a manual recovery; the next campaign will hit them again.

## Goals
- No child PR can merge into anything but `main`.
- Stacked delivery is a documented, chosen option, not an ad hoc switch.
- Campaign state has one documented home and complete statuses.
- Wave planning and worktree landing catch the two failure modes seen in gh:77 mechanically.
- The engine knows when it may edit an approved artifact and how to record it.

## Non-goals
- Automating retargets through the GitHub API in the background (no polling; retarget happens on resume like merge detection).
- Changing playbook-shape campaigns.
- Harness-specific hooks (Claude Code `PreToolUse` etc.) for the worktree guard.
- Rewriting the gh:77 campaign's history or artifacts.

## Acceptance criteria
- **AC1**: Given a stacked child PR whose predecessor has merged, when the campaign resumes, then the procedure merges `main` into the child's branch, re-runs its tests, and retargets the PR's base to `main` before the child may merge; `campaign.md` § Ordered shape states that a child PR's base is `main` whenever it is merged.
- **AC2**: Given stacked delivery, when a child PR (order > 1) is opened, then its body says it is "N of M, stacked on #X" and must be retargeted to `main` before merging.
- **AC3**: Given the stack Deliver gate, when it is presented, then it offers `sequential` (one PR at a time, as today) or `stacked` (all PRs at once, each based on the previous child's branch) delivery, and the choice is recorded in `campaign.json` as `delivery`.
- **AC4**: Given a child built and verified while later children still build, when its status is saved, then it is `verified`; `campaign.md` and `state.md` § Resume list `verified` and resume skips verified members to the next `todo`/`in_progress` one.
- **AC5**: `campaign.md` states the single home of `campaign.json` and the one way each child's branch updates it, so each child's PR diff changes only its own member entry (plus campaign-level gate fields).
- **AC6**: Given a plan where task B links to (or imports) a file task A creates, then the architect role puts B in a later wave via `after: A`; `architect.md` states the rule.
- **AC7**: Given a worktree and a task's `files`, when the offline helper runs, then it exits 0 when every changed path (tracked and untracked) is inside the worktree's fence, and non-zero naming each stray path; it also reports changes found in the main tree during a wave. Unit tests cover a pass, a stray path, and a main-tree write.
- **AC8**: The dispatch prompt and wave landing (`handoff.md`, `efficiency.md`) run that helper before landing, and every engine status check on a worktree uses `git -C <worktree>`.
- **AC9**: Given a synthetic stacked campaign, when the `campaign` eval check runs with `delivery = "stacked"`, then it passes when every member is delivered with a PR and each base is the previous child's branch or `main`, and fails on a member merged into a non-`main` base; existing sequential cases still pass. Tests cover pass and near-miss.
- **AC10**: `SKILL.md` says when the engine may edit an approved artifact itself (wording or path fixes that change no criterion's meaning) and that each such edit is logged in `log.md` and listed at the Deliver gate as a spec change after approval; anything else goes back through the owning role and gate.

## Constraints
- Stdlib-only Python 3.11+, offline; changelog fragment; `aicfg validate` and unit tests pass.
- Files stay short (they load into model context); `campaign.md` is already ~150 lines.
- Existing `campaign.json` files (gh:77) without `delivery` must still read as `sequential`.

## Requirement changes

### Area: campaign-mode
#### MODIFIED: Sequential PRs
The system SHALL deliver an ordered stack `sequential` (only the first PR after approval, each next PR after its predecessor merges) or `stacked` (all PRs at once, each based on the previous child's branch), chosen at the Deliver gate; before any child PR merges, `main` SHALL be merged into its branch, its tests re-run, and its base SHALL be `main`. Upstream review changes and failures propagate as before. (AC1, AC2, AC3)
#### MODIFIED: Campaign state fields
`campaign.json` SHALL record `shape`, `delivery`, `depends_on`, `order`, and statuses `verified` and `waiting`, in one documented home that each child's branch updates only for its own member. (AC4, AC5)
#### ADDED: Worktree fence
Before landing a wave task, the engine SHALL check with a tested offline helper that every changed path is inside the task's worktree and `files`, and that the main tree is unchanged, using `git -C <worktree>`. (AC7, AC8)
#### ADDED: Wave link ordering
The architect SHALL put a task that links to a file another task creates in a later wave. (AC6)

### Area: run-lifecycle
#### ADDED: Engine edits after approval
The engine MAY edit an approved artifact only for wording or path fixes that change no criterion's meaning, and SHALL log each in `log.md` and list it at the Deliver gate. (AC10)

### Area: evals
#### MODIFIED: Campaign check kind
The eval harness SHALL offer a `campaign` check kind that verifies member order and approved spec and plan gates, and for `sequential` delivery first-member-only delivery, for `stacked` delivery every member delivered with a valid base. (AC9)

## Open questions
None. Resolved at the Spec gate:
1. `campaign.json` home (AC5): on the child branch in progress, in `specs/campaign-<slug>/`; each child commits only its own member entry, and `main` is merged in before its PR opens or retargets.
2. Worktree guard (AC7): an engine-run stdlib script `skills/spec-agent/scripts/worktree_fence.py` with unit tests, not a harness hook.
