# Spec: Rename the on-disk names kept for compatibility

Ticket: local:specs/tickets/237-rename-on-disk-names.md · Size: standard · Status: approved

## Problem
Three names that `apply` writes to users' machines still say ai-config: the Codex MCP block
markers in `~/.codex/config.toml`, the OpenCode guard plugin link, and the fetch record inside
each git pack's `.git/`. Renaming any of them blindly would make apply treat its own old output
as foreign: a second Codex block, a second OpenCode guard, or a needless re-fetch.

## Goals
- Write only the brainrc names; read and replace the old ones on the next apply.

## Non-goals
- Removing the deprecated CLI names, `AICFG_HOME` or the legacy home (ticket 238).

## Acceptance criteria
- **AC1**: Given a Codex config with an old-marker block (`# >>> ai-config mcp servers ...` / `# <<< ai-config mcp servers`) and user content around it, when `apply` runs, then the file has exactly one block, with the brainrc markers, the user's content byte-identical, and a second apply changes nothing.
- **AC2**: Given a new Codex config, then `apply` writes the brainrc markers; given a file with both an old and a new block (hand-edited), then both are recognized and one brainrc block remains.
- **AC3**: Given an OpenCode install with `~/.config/opencode/plugins/ai-config-guard.js` linking to the managed guard, when `apply` runs, then `brainrc-guard.js` links to it and the old link is removed; a user's own real file at the old path is left alone (CONFLICT rules as today); `status` is in sync afterwards.
- **AC4**: Given a git pack clone with only `.git/aicfg-fetched.json` matching its config, when `status`/`apply` run, then no re-fetch is planned; apply writes `.git/brainrc-fetched.json` and removes the old record; a mismatching old record still triggers the fetch.
- **AC5**: Given tests/test_old_names.py, then the allowlist rows for these names only cover the old-name recognition code and its tests, and the suite and `validate` pass, also with `XDG_CONFIG_HOME` set.

## Constraints
Stdlib only. No change for users who already have the new names.

## Requirement changes
### Area: aicfg-apply
#### ADDED: Old on-disk names converge
`brainrc apply` SHALL write the brainrc Codex markers, OpenCode guard link and fetch record, and SHALL recognize and replace the old ai-config ones on the next apply without duplicating them. (AC1, AC2, AC3, AC4)

## Open questions
1. Remove the old fetch record after writing the new one? *Default taken:* yes, once the new one is written.
2. Keep recognizing the old names after 0.5.0? *Default taken:* yes; this is on-disk convergence, not a deprecated name users type, so ticket 238 keeps it.

## Proposed split
Not applicable.
