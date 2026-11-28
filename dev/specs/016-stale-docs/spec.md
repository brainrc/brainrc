# Spec: Fix stale docs and align the README pitch with harness support

Ticket: gh:16 · Size: small · Status: approved

## Problem
Three docs say things that are no longer true or describe one person's machine. A new reader of
the README expects every content type (hooks and MCP included) to sync into every harness, which
isn't the case today. Wrong expectations at the first paragraph cost trust in the rest.

## Goals
- Docs describe the repo as it is, with nothing machine-specific.
- The README pitch sets accurate expectations and points to the support table.

## Non-goals
- Changing harness support itself (#19–#22).
- Rewriting the README beyond the opening paragraph.

## Acceptance criteria
- **AC1**: `docs/spec-agent.md` Extending no longer calls Jira planned. It names the existing
  connectors (local, GitHub, Jira).
- **AC2**: `docs/efficiency.md` has no "installed here" or other machine-specific wording.
- **AC3**: The README opening says what syncs everywhere (skills, plus rules and commands where
  the harness supports them), that hooks are Claude Code only and MCP isn't synced yet, and links
  to the harness support table in `docs/formats.md`.
- **AC4**: The roadmap Done item is confirmed done (moved to CHANGELOG by #5), with no change here.
- **AC5**: `validate` and the test suite pass. No other docs reference the stale wording.

## Constraints
Short, plain prose (unslop rules: no semicolons or dashes in new prose).

## Open questions
1. **Size.** This scores `standard` only because it touches 3 files. The edits are a few lines
   each with no design choice. Recommended: say "resize small", which skips the Plan gate (one
   inline task, then Deliver).
