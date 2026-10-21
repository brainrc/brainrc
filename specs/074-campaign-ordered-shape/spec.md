# Spec: Campaign ordered shape

Ticket: gh:74 · Size: set by the engine · Status: draft

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

## Decisions
- Owner-confirmed: all children are built first and approved together at one Deliver gate. PRs then open one by one, each after the previous one merges. They are not opened as stacked PRs.
- Local tickets express dependencies as a `depends_on:` list of `local:` refs in frontmatter (proposed; the architect may adjust the syntax).

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
- **AC13**: Given the sandbox epic of three local tickets (B depends on A, C on B), when its eval case runs, then it checks the order A, B, C, that each child's Spec and Plan gates are approved, and that after delivery only A's branch is recorded as opened.
- **AC14**: `docs/spec-agent.md` describes both shapes.

## Constraints
- Offline only: the eval uses local tickets and no remote. Eval check kinds (`state`, `file`, `command`, `branch`, ...) read one run found by `ticket_ref`.
- Repo rules apply: stdlib-only scripts, files short, changelog fragment, validate and unit tests pass.

## Requirement changes

### Area: campaign-mode
Purpose: Run a set of related tickets as one campaign, in `playbook` or `ordered` shape.
#### ADDED: Shape selection
The system SHALL detect the shape (template check plus depends-on links), show it at the Campaign gate, and honor `--shape`. (AC1, AC2)
#### ADDED: Dependency order
The system SHALL order ordered-shape children topologically and stop at the Campaign gate on a cycle or out-of-epic link. (AC3, AC4)
#### ADDED: Per-child gates and stack delivery
The system SHALL give each ordered child its own Spec and Plan gates, build on the predecessor's branch, and present one Deliver gate for the stack. (AC6, AC7)
#### ADDED: Sequential PRs
The system SHALL open only the first PR after approval and each next PR after its predecessor merges, with `main` merged in and tests re-run; upstream review changes and failures propagate as in AC10 and AC11. (AC8-AC11)
#### ADDED: Campaign state fields
`campaign.json` SHALL record `shape`, `depends_on`, `order`, and status `waiting`. (AC12)

### Area: ticket-connectors
Purpose: Read and update tickets through a uniform connector contract.
#### ADDED: Dependencies read
A connector SHALL offer a read-only `dependencies` operation for campaign ordering; `ticket-github` and `ticket-local` implement it. (AC5)

### Area: run-pointer
#### MODIFIED: Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to `$AICFG_HOME/active-run` (default `~/.config/ai-config/active-run`) at intake, on every resume, and on every checkpoint commit (each gate, block, and done), creating the directory if needed, via `skills/spec-agent/scripts/active_run.py write`. A write failure SHALL warn on stderr and exit 0. In an ordered campaign the pointer SHALL name the child currently in progress. (AC6)

## Open questions
1. How does the engine learn that a predecessor's PR merged (user says so, or it polls)? *It decides when the next PR opens and how a paused campaign resumes. The sandbox has no merge.*
2. Is GitHub's depends-on readable through both `gh` and the MCP server? *The connector contract requires a fallback for each operation.*
3. `--shape ordered` on an epic with no links and a shared template: order by sub-issue order, or refuse? *Defines the override's edge case.*
4. Which run does the eval's `ticket_ref` select for a campaign, and can checks reach every child? *AC13 needs per-child gate evidence, and the eval harness reads one run.*
