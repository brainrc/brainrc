# Spec: read XDG_CONFIG_HOME for opencode

Ticket: gh:134 · Size: standard · Status: approved

## Problem
Someone who points opencode somewhere else with `XDG_CONFIG_HOME` gets brainrc's links, hooks and MCP servers in `~/.config/opencode`,
where opencode never looks, and `doctor` and `uninstall` check the wrong place. Campaign gh:110, playbook v1.

## Goals
- Every opencode path follows `XDG_CONFIG_HOME` when it is set, including its MCP file.
- Unset, empty or relative, the default `~/.config/opencode` is used, as before.

## Non-goals
- Moving links an earlier apply made under the other path (the user re-runs apply after changing the var).
- Changing the harnesses.json manifest format (#126).

## Acceptance criteria
- **AC1**: Given `XDG_CONFIG_HOME` set to an absolute dir where opencode is installed, when the user runs `status`, `apply`, `status`, `doctor` and `uninstall`, then each uses the paths under it, apply writes nothing under `~/.config/opencode`, the second `status` is in sync, doctor is clean, and uninstall takes out what apply added.
- **AC2**: Given `XDG_CONFIG_HOME` unset, then the same commands use `~/.config/opencode`.
- **AC3**: Given `XDG_CONFIG_HOME` set to an empty string (or a relative path), then the same commands use `~/.config/opencode`.
- **AC4**: Given only `opencode.jsonc` in the OpenCode dir, when apply merges MCP servers, then they go into that file, edited in place so its comments and other keys stay, no `opencode.json` is created, and uninstall takes them out again; with both files, `opencode.json` is used.
- **AC5**: Given an `opencode.jsonc` that can't be parsed, then it is left alone and reported.

## Constraints
Stdlib only, Python 3.11+. Same rule as gh:131: only an absolute value counts.

## Requirement changes
### Area: aicfg-apply
#### ADDED: OpenCode config dir from XDG_CONFIG_HOME
`brainrc` SHALL resolve every opencode path in harnesses.toml from `XDG_CONFIG_HOME` when it holds an absolute path, and from `~/.config/opencode` when it is unset, empty or relative, for `status`, `apply`, `doctor` and `uninstall` alike. (AC1, AC2, AC3, AC4, AC5)

## Open questions
None. Defaults taken under the auto run:
1. A relative value is ignored, as gh:131 does for XDG_CONFIG_HOME.
2. A value under `~` is stored with `~`, so hook commands and the manifest stay portable.

## Proposed split
