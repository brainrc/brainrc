# Plan: OpenCode gets real subagents

No new dependency. New harness key `agents_format` (harnesses.toml) and a new render folder
`$AICFG_HOME/opencode/agents/`; both documented.

## Approach
- `opencode_agent(path) -> str`: frontmatter → `description`, `mode: subagent`, and a
  `permission:` block of `deny` for each OpenCode key the Claude `tools` list doesn't cover.
  Body unchanged. Pure function, so it's easy to test.
- `rendered_agents(srcs) -> dict[Path, str]` for every agent in the enabled sources, under
  `aicfg_home() / "opencode" / "agents"`, only when an enabled harness sets
  `agents_format = "opencode"`.
- `cmd_sync(apply)`: write those renders next to `instructions.md`, delete render files no longer
  wanted. `plan()`: for such a harness, an agent link's source is its render.
  `_managed_target`: renders count as managed, so stale links get pruned.
- `_render_findings` (doctor): missing or stale agent renders, like `instructions.md`.
- `load_harnesses`-time check: an unknown `agents_format` is a ConfigError.

## Tasks
| id | title | agent | files | criteria |
|---|---|---|---|---|
| T1 | tests first: conversion, render+link, prune, doctor | implementer | tests/test_aicfg.py | AC1–AC4 |
| T2 | aicfg: convert, render, link, prune, doctor | implementer | scripts/aicfg.py | AC1–AC3 |
| T3 | harnesses.toml `[opencode]` agents | implementer | harnesses.toml | AC1 |
| T4 | real OpenCode `agent list` in a fake HOME | implementer | none | AC4 |
| T5 | docs and release | implementer | docs/*, README.md, CHANGELOG.md, VERSION | AC5 |
