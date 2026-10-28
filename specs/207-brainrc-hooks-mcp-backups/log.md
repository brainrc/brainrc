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

## code-reviewer · T2 · done
**Findings:** LOW Windows backslashes not matched (harmless, POSIX targets); LOW mixed-case pack names (e.g. ai-config-Acme) not matched as old-name entries; pre-existing, follow-up (validate pack names). 531 OK.

## code-reviewer · T3 · done (attempt 2)
**Findings:** MEDIUM no corrupt-former-record test → engine added one (3 corrupt forms: nothing claimed, CONFLICT kept, file untouched); LOW shadow check on non-list → made exact. Landed 01ec260.

## implementer · T4 · done
Suite 551 OK; validate OK. Within fence.

## code-reviewer · T4 · done (no CRITICAL/HIGH)
**Findings:** MEDIUM AC3 installed-mode path untested → T5; MEDIUM no Cursor hooks.json convergence from old names → T5; LOW HookDirRenameTest inherits PackSyncTest (12 reruns) → follow-up. Commit 5de6abc.

## implementer · T5 · done
4 end-to-end tests; no T1-T4 bugs. Suite 555 OK (also with CI's XDG_CONFIG_HOME). Commit 0eccf28.

## security-reviewer · branch · done (no CRITICAL/HIGH)
**Findings:** MEDIUM loose backup glob could prune a user's look-alike → F1 bbdc408 (red then green); LOW unanchored ownership substring (pre-existing) → follow-up.

## verifier (engine) · verify · done
13/13 criteria pass; 556 OK with and without XDG_CONFIG_HOME. Living area aicfg-apply applied. PR body and ticket comment drafted.

## engine · Deliver gate · auto-approved
2026-10-28T13:57:44Z
⛔ Deliver gate: 207-brainrc-hooks-mcp-backups
Summary: hooks dir and backups renamed to brainrc with old names converging on one apply; MCP records in former homes honored. 13/13 criteria; security review clean of CRITICAL/HIGH.
Decide: push 207-brainrc-hooks-mcp-backups, open a draft PR from pr-body.md; ticket comment stays a draft (auto).
Artifacts: specs/207-brainrc-hooks-mcp-backups/{verify.md,pr-body.md,ticket-comment.md}

## engine · deliver · done
2026-10-28T14:09:45Z
Pushed; draft PR #233; ticket comment kept as a draft (auto). Subscribed.
