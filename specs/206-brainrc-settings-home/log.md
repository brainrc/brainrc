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

## engine · Plan gate · approved
2026-10-28T03:27:11Z
Owner approved (patch bump). Tasks run sequentially in the main tree.

## test-writer · T1 · done
**Evidence:** 16 tests, 14 fail on assertions (no ~/.config/brainrc render, no warning); 2 --version guards pass. Within fence.

## code-reviewer (engine inline) · T1 · done
**Findings:** none; every case uses a temp HOME and an explicit env. Commit 374b004.

## implementer · T2 · done
**Evidence:** suite 472 OK, validate OK. Within fence.

## engine · spec change after approval (owner consented)
2026-10-28T03:37:13Z
Engine found the approved resolution paragraph skipped the legacy fallback whenever XDG_CONFIG_HOME was set (an XDG_CONFIG_HOME=~/.config machine would ignore an old install silently, contradicting resolved question 2). Owner chose "use the old dir and warn". Amended the spec paragraph and AC3; replaced test_ac3_absolute_xdg_beats_legacy_dir_without_warning with two tests (legacy used + warns; XDG home present wins); home_origin fixed. tests/test_settings_home.py added to T2's files (scope extension, approved with the change). +1 intervention.

## code-reviewer · T2 · done (no CRITICAL/HIGH)
**Findings:** MEDIUM no direct tests for new_home/former_homes and edge cases → added 5 in-process tests (engine); LOW lexical compare in former_homes → _same_dir with samefile (mutation check: symlink test fails without it); LOW BrainrcCommandTest uses the real HOME (pre-existing, follow-up). Suite 478 OK. Commit 914bf27.

## implementer · T3 · done
**Evidence:** red 3 errors with the check off; 6/6 green; suite 484 OK; validate OK. Within fence.
Engine: the unused-old-dir fix said a bare `rm -r`; an old dir may hold unmigrated settings (migrate refuses a non-empty target), so the fix now says to move what is still needed first. Review batched. Commit 0ba9317.
