# Spec: Validate accepts full model IDs and the Task tool

Ticket: gh:202 · Size: small · Status: approved

## Problem
`validate` accepts an agent's `model` only as `haiku`, `sonnet`, `opus`, or `inherit`, so a pack
agent pinned to a full Claude model ID (`claude-sonnet-5-5`) fails validation even though Claude
Code accepts it. `tools: Task` (the subagent tool, which the OpenCode renderer already maps to
`task`) fails as an unknown tool.

## Goals
- Agents may pin a full Claude model ID and list `Task`.

## Non-goals
- Checking that a model ID exists or is current; non-Claude model names.
- Changing the core convention (core agents keep the aliases).

## Acceptance criteria
- **AC1**: Given an agent with `model: claude-sonnet-5-5` (any `claude-` ID of lowercase letters,
  digits, dots, and hyphens), when `validate` runs, then it reports no model error.
- **AC2**: Given an agent with `tools: Read, Task`, when `validate` runs, then it reports no tool error.
- **AC3**: Given an agent with `model: gpt-9` or `tools: Read, Nope`, when `validate` runs, then it
  still fails with ``unknown model `gpt-9` `` or ``unknown tool `Nope` ``.

## Constraints
None known.

## Requirement changes

### Area: aicfg-config
#### ADDED: Agent model and tool names
`aicfg validate` SHALL accept an agent `model` that is `haiku`, `sonnet`, `opus`, `inherit`, or
a full `claude-` model ID, and `Task` among its `tools`, and SHALL reject any other model or
tool name (except `mcp__` tools). (AC1, AC2, AC3)

## Open questions
None.
