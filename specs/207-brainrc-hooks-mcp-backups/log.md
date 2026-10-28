# Log: 207-brainrc-hooks-mcp-backups

## engine · intake · done
2026-10-28T05:08:03Z
**Did:** Branch from main (v0.4.2). Owner: "Do 207 auto" → auto true. Size standard (config, settings, mcp, plan, overrides fragments, tests; one design choice: how old-name entries are recognized and replaced), mode subagent, domain scripting, offline only. Baseline 525 OK.

## analyst · spec · done
13 criteria, 5 open questions with defaults; no instructions found in the ticket. Engine ran living_specs check → exit 0 (aicfg-apply).

## engine · Spec gate · auto-approved
2026-10-28T05:09:32Z
⛔ Spec gate: 207-brainrc-hooks-mcp-backups
Summary: new hooks dirs hooks/brainrc(-<pack>); OWNED_HOOK matches both names, one apply replaces old entries and removes old hook links; MCP ownership honors records in the home and former homes; backups .bak-brainrc-*, old .bak-aicfg-* count toward the 5 kept. 13 criteria, defaults taken for 5 questions.
Decide: criteria and defaults.
Artifacts: specs/207-brainrc-hooks-mcp-backups/spec.md
