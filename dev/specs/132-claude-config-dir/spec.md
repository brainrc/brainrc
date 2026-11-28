# Spec: read CLAUDE_CONFIG_DIR for claude

Ticket: gh:132 · Size: standard · Status: approved

## Problem
Someone who points claude somewhere else with `CLAUDE_CONFIG_DIR` gets brainrc's links, hooks and MCP servers in `~/.claude`,
where claude never looks, and `doctor` and `uninstall` check the wrong place. Campaign gh:110, playbook v1.

## Goals
- Every claude path follows `CLAUDE_CONFIG_DIR` when it is set, including `.claude.json`, which Claude Code keeps inside the dir.
- Unset, empty or relative, the default `~/.claude` is used, as before.

## Non-goals
- Moving links an earlier apply made under the other path (the user re-runs apply after changing the var).
- Changing the harnesses.json manifest format (#126).

## Acceptance criteria
- **AC1**: Given `CLAUDE_CONFIG_DIR` set to an absolute dir where claude is installed, when the user runs `status`, `apply`, `status`, `doctor` and `uninstall`, then each uses the paths under it, apply writes nothing under `~/.claude`, the second `status` is in sync, doctor is clean, and uninstall takes out what apply added.
- **AC2**: Given `CLAUDE_CONFIG_DIR` unset, then the same commands use `~/.claude`.
- **AC3**: Given `CLAUDE_CONFIG_DIR` set to an empty string (or a relative path), then the same commands use `~/.claude`.
- **AC4**: Given CLAUDE_CONFIG_DIR, when apply merges MCP servers and hooks, then they go to `$CLAUDE_CONFIG_DIR/.claude.json` and `$CLAUDE_CONFIG_DIR/settings.json`, hook commands point at `$CLAUDE_CONFIG_DIR/hooks/brainrc`, and doctor reads Claude Code's plugin list from `$CLAUDE_CONFIG_DIR/plugins`.
- **AC5**: Given any of the harness vars set while the test suite runs, then no test writes into that dir.

## Constraints
Stdlib only, Python 3.11+. Same rule as gh:131: only an absolute value counts.

## Requirement changes
### Area: aicfg-apply
#### ADDED: Claude Code config dir from CLAUDE_CONFIG_DIR
`brainrc` SHALL resolve every claude path in harnesses.toml from `CLAUDE_CONFIG_DIR` when it holds an absolute path, and from `~/.claude` when it is unset, empty or relative, for `status`, `apply`, `doctor` and `uninstall` alike. (AC1, AC2, AC3, AC4)

## Open questions
None. Defaults taken under the auto run:
1. A relative value is ignored, as gh:131 does for XDG_CONFIG_HOME.
2. A value under `~` is stored with `~`, so hook commands and the manifest stay portable.

## Proposed split
