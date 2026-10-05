# Spec: Ticket-connector contract, validated

Ticket: gh:8 · Size: standard · Status: draft

## Problem
spec-agent talks to tickets only through connector skills (`ticket-local`, `ticket-github`,
`ticket-jira`, or a pack's own). Which operations a connector must provide, which ones touch the
outside world, and which gate allows each live only in the existing skills by convention. A pack
author writing a connector has to reverse-engineer them, and nothing tells them a required
operation is missing until a run fails at Deliver.

## Goals
- One written contract that both spec-agent and connector authors read.
- `validate` catches a connector missing a required operation.
- A recorded decision on one vs many ticket connectors per pack.

## Non-goals
- New connectors (Linear, GitLab, ...).
- Checking that a connector's operations actually work. Behavioural tests belong to #6.
- Changing what the existing connectors do.

## Acceptance criteria
- **AC1**: `skills/spec-agent/references/connectors.md` defines each operation: name, required
  or optional, read-only or outward, the stage and gate that allow it, and what it returns or
  writes. Operations: `fetch`, `list`, `claim`, `comment`, `transition`, `link_pr`, plus the
  local-only delivery behaviour.
- **AC2**: The contract says operations may be implemented through a CLI or an MCP server, and
  `ticket-github` lists the MCP equivalent of each `gh` command (the 005 retro's gap).
- **AC3**: Given a connector skill (any core `ticket-*` skill, or a skill named by a pack's
  `[extensions.ticket].connector`) with no `##` heading naming `fetch`, `comment`,
  `transition`, or `link_pr`, when `validate` runs, then it fails naming the skill and the
  missing operations. One heading may name several operations
  (`## comment / transition / link_pr`).
- **AC4**: The three core connectors and the example pack pass `validate` unchanged in behaviour.
- **AC5**: `docs/spec-agent.md` Extending links the contract, and spec-agent's SKILL.md points
  to it for connector questions.
- **AC6**: The one-connector-per-pack limit is documented in `docs/packs.md` with the reason.
- **AC7**: Pack contract change: `## 0.3.0` CHANGELOG entry tagged **[pack contract]**,
  `VERSION` 0.3.0, example pack pin `">=0.3, <0.4"`. Suite and both validates pass.

## Constraints
Stdlib only. Contract doc short (it's read at intake and Deliver).

## Open questions
Each has a recommended default; approving accepts them all.
1. **One connector per pack, or a list?** Default: keep one, documented. *Matters because* a
   list changes the `[extensions.ticket]` schema for every pack, and no pack needs two yet.
2. **Version?** Default: `0.3.0`. A pack connector missing a required section now fails
   `validate` and blocks `apply`, which is breaking under the policy.
3. **MCP equivalents (AC2) in this ticket?** Default: yes. It's small and the contract is where
   it belongs. Drop it if you'd rather keep this ticket to the contract and the check.
