# Spec: Render rules and extensions to $AICFG_HOME

Ticket: gh:50 (step 1 of 6; refs) · Size: standard (aicfg paths, spec-agent text, 6 docs; one compatibility choice) · Status: approved

## Problem
`apply` writes `dist/instructions.md` and `skills/spec-agent/references/extensions.md` into the
checkout. A package install (plugin cache, Gemini extension dir) is read-only and has no
`aicfg` checkout, so neither file can exist there. Every later #50 step needs one place,
outside any checkout, where rendered output lives.

## Acceptance criteria
- **AC1** `aicfg_home()` = `$AICFG_HOME` if set, else `~/.config/ai-config`. `apply` writes
  `instructions.md` and `extensions.md` there.
- **AC2** Each harness's `instructions` link points at `$AICFG_HOME/instructions.md`. An existing
  link to `dist/instructions.md` shows as `UPDATE` and `apply` re-points it; a link to the new path
  for a disabled harness is pruned as today.
- **AC3** `apply` removes the old generated `dist/instructions.md` (nothing else reads it).
- **AC4** spec-agent (`SKILL.md`, `lifecycle.md`, `campaign.md`) and `ticket-jira` read
  `$AICFG_HOME/extensions.md` (default `~/.config/ai-config/extensions.md`), falling back to
  `references/extensions.md`.
- **AC5** `doctor` checks the files in `$AICFG_HOME` (stale or missing → `apply`), shown with `~`.
- **AC6** Docs: README, `harnesses.toml` comment, `docs/architecture.md`, `docs/packs.md`,
  `docs/troubleshooting.md`, `docs/tutorial.md` (and its run script if it greps the old path).
- **AC7** Tests updated and added: apply writes both files under a fake `AICFG_HOME`; the old
  `dist` link is updated; the old file is removed; doctor flags a stale `$AICFG_HOME` render.
  The tutorial script passes. VERSION and CHANGELOG per the choice below; `aicfg plugin` run.

## Compatibility choice (decide at this gate)
`extensions.md` at `skills/spec-agent/references/` is part of the rendered pack contract, and a
pack's own skills could read that path.
- **A (recommended): also keep writing the in-repo copy, for now.** Nothing breaks, so this is
  PATCH 0.3.16. spec-agent reads `$AICFG_HOME` first. The CHANGELOG marks the in-repo copy
  deprecated; a later MINOR removes it.
- **B: move it.** `apply` stops writing it and deletes it. Cleaner, but it's a breaking
  **[pack contract]** change: MINOR 0.4.0, and every pack must widen `requires_core` past `<0.4`.

## Not in this step
Hook fragments stay rendered into settings by the existing merge. Loading the rules in a package
(Claude `SessionStart`, Gemini `GEMINI.md`) is a later #50 step.

## Open questions
None. Option A approved at the Spec gate.
