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

## architect · plan · done
5 tasks (T1-T3 independent, T4 after T1+T2, T5 after T3+T4); Callouts: contract (hooks_dir, .bak-brainrc-*), data (first apply converges), destructive (old hook symlinks removed).

## engine · blocked · auto hard stop
2026-10-28T05:12:28Z
Plan Callouts are not none; the Plan gate needs the owner. Nothing pushed.

## engine · Plan gate · approved by owner
2026-10-28T13:00:29Z
Owner: "Approve continue auto" (callouts approved; auto continues). +1 intervention.

## engine · wave 1 (T1, T2, T3) · handoffs in
- T1 done: backups .bak-brainrc, prune across both names by stamp. Red 3, suite 528 OK, validate OK. Landed b907aaa.
- T2 done: OWNED_HOOK matches both names by path component; OWNED_HOOK_MARKER /hooks/brainrc/. Red 3, suite 528 OK. Landed 578766c; committed before its review (engine ordering slip), review running now.
- T3: union of records; engine's brief contradicted spec AC7 and the plan (resolved home wins per file; `[]` kept while a former home holds the key). Re-dispatched as attempt 2 (engine's error).
- Fence: worktree STRAY hits were only .runs logs the brief told them to save; patches exclude specs/.
