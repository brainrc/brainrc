# Spec: read CODEX_HOME for codex

Ticket: gh:133 · Size: standard · Status: approved

## Problem
Someone who points codex somewhere else with `CODEX_HOME` gets brainrc's links, hooks and MCP servers in `~/.codex`,
where codex never looks, and `doctor` and `uninstall` check the wrong place. Campaign gh:110, playbook v1.

## Goals
- Every codex path follows `CODEX_HOME` when it is set, including `config.toml`.
- Unset, empty or relative, the default `~/.codex` is used, as before.

## Non-goals
- Moving links an earlier apply made under the other path (the user re-runs apply after changing the var).
- Changing the harnesses.json manifest format (#126).

## Acceptance criteria
- **AC1**: Given `CODEX_HOME` set to an absolute dir where codex is installed, when the user runs `status`, `apply`, `status`, `doctor` and `uninstall`, then each uses the paths under it, apply writes nothing under `~/.codex`, the second `status` is in sync, doctor is clean, and uninstall takes out what apply added.
- **AC2**: Given `CODEX_HOME` unset, then the same commands use `~/.codex`.
- **AC3**: Given `CODEX_HOME` set to an empty string (or a relative path), then the same commands use `~/.codex`.
- **AC4**: Given CODEX_HOME under `~`, then the manifest records the path with `~`.

## Constraints
Stdlib only, Python 3.11+. Same rule as gh:131: only an absolute value counts.

## Requirement changes
### Area: aicfg-apply
#### ADDED: Codex home from CODEX_HOME
`brainrc` SHALL resolve every codex path in harnesses.toml from `CODEX_HOME` when it holds an absolute path, and from `~/.codex` when it is unset, empty or relative, for `status`, `apply`, `doctor` and `uninstall` alike. (AC1, AC2, AC3, AC4)

## Open questions
None. Defaults taken under the auto run:
1. A relative value is ignored, as gh:131 does for XDG_CONFIG_HOME.
2. A value under `~` is stored with `~`, so hook commands and the manifest stay portable.

## Proposed split
