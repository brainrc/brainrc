# Log: 206-brainrc-settings-home

## engine · intake · done
2026-10-28T03:15:37Z
**Did:** Branch 206-brainrc-settings-home from main (v0.4.0, #230 merged). Size standard (config, cli, doctor, docs; a new `migrate` command and env var: contract change; migration of user files), mode subagent, domain scripting, offline only, auto false. Baseline below.
**Evidence:** baseline on main failed 6 tests (example pack requires_core <0.4 vs core 0.4.0, caused by #230's minor bump); fix PR #231 merged into this branch; baseline now 456 OK.

## analyst · spec · done
**Did:** spec.md: 16 criteria, 7 open questions with defaults; folds in #131 (XDG). Engine ran living_specs check → exit 0 (aicfg-config, aicfg-apply, run-pointer).
Merged origin/main (#231 fix, v0.4.1).

## engine · Spec gate · presented
2026-10-28T03:23:27Z

## engine · Spec gate · approved
2026-10-28T03:24:09Z
Owner approved with all recommended defaults (XDG folded in, closes #131; doctor WARN; symlinked dir moved as a link).

## architect · plan · done
**Did:** plan.md, 6 tasks; callouts: BRAINRC_HOME/XDG/migrate contract, user-data move (atomic rename, EXDEV copy-then-remove, rollback documented), bump patch tagged [pack contract].

## engine · Plan gate · presented
2026-10-28T03:26:49Z
