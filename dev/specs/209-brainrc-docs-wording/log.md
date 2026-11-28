# Log: 209-brainrc-docs-wording

## engine · intake · done
2026-10-28T17:12:47Z
**Did:** Branch from main (v0.4.4), carrying #208's record. Owner: "I don't want alerted or decisions until deliver gate" → Spec and Plan auto-approved, open questions and any Callout take their defaults and are listed at the Deliver gate, which stops for the owner. Size: about 40 files mention the old names, mostly mechanical text and deliberate compatibility code; sized standard (not large/split) as the default under that instruction, to be listed at Deliver. Mode subagent, domain scripting, offline only.

## analyst · spec · done
8 criteria; the Done-when grep becomes a test against a closed allowlist (path + regex + reason, stale entries fail); tutorial run offline via specs/013-tutorial/run-tutorial.sh; 5 open questions with defaults (rename test_aicfg.py and internal identifiers; keep living spec file names; keep Codex markers, OpenCode guard link name, .git/aicfg-fetched.json; size standard).

## engine · Spec gate · auto-approved (owner: no decisions until Deliver)
2026-10-28T17:15:37Z

## engine · Spec gate approval withdrawn
living_specs.py check failed (text outside a requirement block), and the MODIFIED blocks hold shorthand ("brainrc replaces aicfg") instead of full requirement text, which apply would write over 12 living requirements. Back to the analyst.

## analyst · spec · done (revision)
Requirement changes fixed: full requirement text in each MODIFIED block. Engine: living_specs check exit 0; each MODIFIED block equals the living text except the tool name (and the dropped #209 sentence).

## engine · Spec gate · auto-approved (owner: no decisions until Deliver)
2026-10-28T17:16:48Z

## architect · plan · done
9 tasks; T1 allowlist test first; T2-T6 parallel; T7, T8 code; T9 fragment + allowlist reconcile. Callouts (listed at Deliver, not stopping per owner): identifier rename, home_origin value, guard/banner text, pre-commit hook id, temp names, T6 ~400 mechanical lines.

## engine · Plan gate · auto-approved (owner: no decisions until Deliver)
2026-10-28T17:20:34Z
Engine default before approval: keep `aicfg_home` as a one-line deprecated alias until 0.5.0 (import aicfg compatibility). Pre-commit hook is repo-local (.pre-commit-config.yaml), so its id rename affects only SKIP= users.

## implementer · T1 · done
Red as designed: 566 offending lines, 7 stale rows (test_brainrc.py rows until T6). Commit 1ebec07. Wave 1: T2, T3 in worktrees.

## wave 1 (T2, T3) landed
T2 7c7f7dc (10 docs), T3 a1d0701 (README, AGENTS, CONTRIBUTING); fences OK. Wave 2: T4, T5.

## wave 2 (T4, T5) landed
T4 fba2f9f (config changes comment-only except the planned pre-commit hook), T5 4d8c02d. T6 next (main tree).

## implementer · T6 · done
581 tests before and after; only test_old_names fails (expected until T9). Engine review (inline): git sees a rename; changes are alias/fixture names only. Commit f27163d.

## implementer · T7 · done
Suite: only test_old_names fails. Engine review (inline): diff is strings, docstrings and comments only; no banner-based recognition exists. Two intentional old-name docstrings (cli.py, doctor.py) left for T9. Commit 8ae2f9f.

## implementer · T8 · done
582 tests; only test_old_names fails. Alias kept and tested.

## code-reviewer · T8 · done
No findings; pure rename. Commit 61c2819.

## engine · T9 scope widened before dispatch
Added tests/test_brainrc.py, brainrc/cli.py, brainrc/doctor.py, docs/install.md, skills/spec-agent/SKILL.md so T9 can reword or allowlist the last hits (listed at Deliver; owner asked for no decisions before it).

## implementer · T9 · done
test_old_names OK; suite 582 OK (1 skip); validate OK. Touched only 4 of its widened files. Commit 4ece048.

## code-reviewer · batch · changes-requested
HIGH fragment claimed all old names warn; MEDIUM fragment missing bullets; MEDIUM package-wide allowlist rows (a stale $AICFG_HOME docstring slipped through); LOW docs OLD_LINE rows (accepted). → F1 c77a2e6.

## verifier (engine) · verify · done
8/8 criteria; 582 OK with and without XDG; tutorial ran clean. Living areas applied.

## engine · Deliver gate · presented to the owner
2026-10-28T17:53:05Z

## engine · Deliver gate · approved by owner
2026-10-28T19:59:21Z
Owner: "Approve: ready PR + comment".

## engine · deliver · done
2026-10-28T20:16:13Z
Pushed; PR #235 (ready for review); commented on #209; subscribed.
