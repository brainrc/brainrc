# Spec: Campaign ordered shape

Ticket: gh:74 · Size: standard · Status: approved

## Problem
`/work --campaign` accepts only near-identical tickets. An epic of different, dependent children fails the template check and every child is rejected as a deviant, so the user sequences runs and PRs by hand. Campaigns need a second shape that builds children in dependency order and delivers them as one reviewed stack.

## Goals
- Two shapes, `playbook` (unchanged) and `ordered`, chosen at the Campaign gate and overridable with `--shape`.
- Children are built in dependency order, each with its own Spec and Plan gates.
- One Deliver gate for the stack, then PRs open one at a time as each predecessor merges.

## Non-goals
- Stacked PRs opened all at once; dependencies across repos; Jira dependency links.
- Changing playbook-shape behavior or its docs sections.
- Orchestration-mod display (#73).
- Background polling for merges.

## Decisions
- Owner-confirmed: all children are built first and approved together at one Deliver gate. PRs then open one by one, each after the previous one merges. They are not opened as stacked PRs.
- Local tickets express dependencies as a `depends_on:` list of `local:` refs in frontmatter (proposed; the architect may adjust the syntax).
- Merge detection is pull-based on resume: `/work --campaign <ref>` (or /spec-resume) reads each waiting predecessor's PR state through the connector (ticket-github: `gh pr view --json state` or the MCP equivalent, read-only). The user saying "merged" also counts. No background polling.
- GitHub dependencies: use the issue dependency API (`gh api repos/<o>/<r>/issues/<n>/dependencies/blocked_by`) when available; otherwise fall back to `Depends on #N` lines in the issue body (works with MCP too). The Campaign gate states which source was used.
- `--shape ordered` on an epic with no links is allowed: order is the sub-issue order, stated at the gate.
- Eval: a new `campaign` check kind in `scripts/evals.py` (tests in `tests/test_evals.py`) reads `campaign.json` plus each member's `state.json`.

## Acceptance criteria
- **AC1**: Given an epic whose children differ or have depends-on links, when the Campaign gate is presented, then it states shape `ordered` and the child order. Given three children sharing one template and no links, then it states `playbook`.
- **AC2**: Given `--shape playbook|ordered`, when the Campaign gate is presented, then that shape is used and shown instead of the detected one.
- **AC3**: Given children with depends-on links, when ordering, then they are sorted topologically; children without links keep the epic's order.
- **AC4**: Given a cycle or a link to a ticket outside the epic, when the Campaign gate is reached, then the run stops there and lists the offending links.
- **AC5**: Given `ticket-github`, when asked for `dependencies`, then it returns a child's depends-on links read-only. Given `ticket-local`, then it returns the `depends_on:` refs.
- **AC6**: Given an ordered campaign, when children build, then each has its own `specs/<slug>/` with Spec and Plan gates presented, and child N's branch starts from child N-1's branch.
- **AC7**: Given every child verified, when delivering, then one Deliver gate lists every child's outward actions verbatim in merge order.
- **AC8**: Given approval, when delivery begins, then only child 1's PR opens (with delivery local-only/no remote: only child 1's branch is recorded as its PR) and later children are `waiting`.
- **AC9**: Given a predecessor's PR merged, when the next child is released, then `main` is merged into its branch, its tests re-run, and only then its PR opens. The PR body states "N of M, after #X" and links the epic.
- **AC10**: Given an earlier child's PR changed in review, when later PRs are not yet open, then the change is merged into the later branches and their tests re-run first.
- **AC11**: Given a child fails or is blocked, then every later child pauses and earlier ones are unaffected. Existing campaign stops still apply.
- **AC12**: Given an ordered campaign, then `campaign.json` holds `shape`, per-member `depends_on` and `order`, and member status may be `waiting`; `state.md` and `campaign.md` document them, and `campaign.md` has an `## Ordered shape` section that a playbook run need not load.
- **AC13**: Given the sandbox epic of three local tickets (B depends on A, C on B), when its eval case runs, then it checks the order A, B, C, that each child's Spec and Plan gates are approved, and that after delivery only A's branch is recorded as opened (see AC18).
- **AC14**: `docs/spec-agent.md` describes both shapes.
- **AC15**: Given an ordered campaign with `waiting` members, when `/work --campaign <ref>` or /spec-resume runs, then the engine reads each waiting predecessor's PR state read-only through the connector and releases the next child only if it is merged or the user says "merged". Nothing polls in the background.
- **AC16**: Given a GitHub epic, when dependencies are read, then the issue dependency API is used if available, else `Depends on #N` lines in the issue body; the Campaign gate states which source was used.
- **AC17**: Given `--shape ordered` on an epic with no links, when the Campaign gate is presented, then the run proceeds in sub-issue order and the gate states that order.
- **AC18**: Given a `campaign` eval check, when it runs against a campaign run, then it reads `campaign.json` and each member's `state.json` and fails unless the order matches, every member's spec and plan gates are approved, and after delivery only the first member's branch/PR is recorded. `tests/test_evals.py` covers a passing case and failing near-misses.

## Constraints
- Offline only: the eval uses local tickets and no remote, so merge detection is not exercised there. Existing check kinds (`state`, `file`, `command`, `branch`, ...) read one run found by `ticket_ref`; the `campaign` kind reaches the member runs.
- Repo rules apply: stdlib-only scripts, files short, changelog fragment, validate and unit tests pass.

## Requirement changes

### Area: campaign-mode
Purpose: Run a set of related tickets as one campaign, in `playbook` or `ordered` shape.
#### ADDED: Shape selection
The system SHALL detect the shape (template check plus depends-on links), show it at the Campaign gate, and honor `--shape`, including `ordered` on an epic with no links (sub-issue order). (AC1, AC2, AC17)
#### ADDED: Dependency order
The system SHALL order ordered-shape children topologically and stop at the Campaign gate on a cycle or out-of-epic link. (AC3, AC4)
#### ADDED: Per-child gates and stack delivery
The system SHALL give each ordered child its own Spec and Plan gates, build on the predecessor's branch, and present one Deliver gate for the stack. (AC6, AC7)
#### ADDED: Sequential PRs
The system SHALL open only the first PR after approval and each next PR after its predecessor merges, with `main` merged in and tests re-run; upstream review changes and failures propagate as in AC10 and AC11. (AC8-AC11)
#### ADDED: Merge detection
The system SHALL learn of a predecessor's merge by reading its PR state on resume, or from the user, and SHALL NOT poll. (AC15)
#### ADDED: Campaign state fields
`campaign.json` SHALL record `shape`, `depends_on`, `order`, and status `waiting`. (AC12)

### Area: ticket-connectors
Purpose: Read and update tickets through a uniform connector contract.
#### ADDED: Dependencies read
A connector SHALL offer a read-only `dependencies` operation for campaign ordering; `ticket-local` reads `depends_on:`; `ticket-github` uses the dependency API with a `Depends on #N` body fallback and reports the source used. (AC5, AC16)

### Area: run-pointer
#### MODIFIED: Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to `$AICFG_HOME/active-run` (default `~/.config/ai-config/active-run`) at intake, on every resume, and on every checkpoint commit (each gate, block, and done), creating the directory if needed, via `skills/spec-agent/scripts/active_run.py write`. A write failure SHALL warn on stderr and exit 0. In an ordered campaign the pointer SHALL name the child currently in progress. (AC6)

### Area: evals
Purpose: Check workflow runs against expected outcomes offline.
#### ADDED: Campaign check kind
The eval harness SHALL offer a `campaign` check kind that verifies member order, approved spec and plan gates, and first-member-only delivery. (AC13, AC18)

## Open questions
None.
