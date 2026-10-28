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

## implementer · T4 · done (attempt 1)
**Evidence:** red 7/12; green 12 OK; suite 496 OK; validate OK. Within fence.

## security-reviewer · T4 · done (no CRITICAL/HIGH)
**Findings:** MEDIUM no path sanity (AICFG_HOME=$HOME or / with EXDEV copies then rmtrees it; relative env values; target inside source); MEDIUM migrate locks source/apply.lock while apply locks aicfg_home()/apply.lock (differ when both env vars set); LOW predictable temp name; LOW temp dir mode briefly wider than source; LOW former_homes re-point (symlinks only).

## code-reviewer · T4 · changes-requested
**Findings:** HIGH EXDEV + symlinked source materializes a real copy (breaks Q7); MEDIUM concurrent apply into an empty existing target → ENOTEMPTY traceback; MEDIUM uncaught OSError paths (source is a file, target symlink, target inside source); MEDIUM rmtree(source) failure after move leaves partial source and skips apply; MEDIUM plan.py former-home re-point applies to any link into the old dir on every apply; LOW lock gap before apply (accepted); LOW usage alignment; LOW relative symlink source.
→ T4 attempt 2.

## implementer · T4 · done (attempt 2)
**Evidence:** mutation red 3 tests; test_migrate 29 OK; suite 513 OK; validate OK.

## security-reviewer · T4 re-review · done
**Findings:** prior MEDIUMs fixed. LOW ancestor of $HOME not refused; LOW generic marker names; LOW same-device relative symlink dangles.

## code-reviewer · T4 re-review · done
**Findings:** prior HIGH/MEDIUMs fixed. LOW markers stricter than AC7 (active-run); LOW same-device symlink onto empty target → ENOTDIR; LOW same-device relative symlink; LOW Windows open-file caveat (follow-up).

## engine · T4 LOW fixes
Refuse a source at or above $HOME; markers are brainrc-only names (+ active-run) or rules/*.local.md; a symlinked source always moves by recreating the link (any device, empty target accepted). 4 tests added; each fails under a mutation reverting its fix. Suite 517 OK. Commit 209a4de.

## implementer · T5 · done
**Evidence:** red 12/24; suite 524 OK; validate OK. Within fence. Engine shortened the SKILL.md/state.md home lines (context cost). Review batched. Commit edb6e9f.

## engine · T6 · done
Docs (install, packs, formats) and the patch [pack contract] fragment written inline. Suite 524 OK; validate OK. Commit 434e68d.

## code-reviewer · batch · done (no CRITICAL/HIGH)
**Findings:** MEDIUM doctor "unused, rm -r" also when the new home is missing/empty and the old dir holds the only data → F1 (6c0af5d, red then green); LOW exit-code test patches doctor_findings (accepted); LOW docs/architecture.md, docs/harness-packages.md still named $AICFG_HOME as default → F2 (303ada3); LOW patch bump with [pack contract] → owner approved patch at the Plan gate. Suite 525 OK.

## verifier (engine) · verify · done
2026-10-28T04:50:21Z
16/16 criteria pass; installed end-to-end migrate run (see verify.md). Living areas applied.

## engine · document · done
PR body and ticket comment drafted inline.

## engine · Deliver gate · presented
2026-10-28T04:50:44Z

## engine · Deliver gate · approved
2026-10-28T04:51:26Z
Owner approved, PR ready for review (not draft).

## engine · deliver · done
2026-10-28T04:55:21Z
Pushed; PR #232 (ready for review); commented on #206; subscribed.

## engine · watch · CI red on #232
2026-10-28T04:58:43Z
validate failed: test_defaults_to_config_dir_under_home read the runner's XDG_CONFIG_HOME (GitHub sets it). Reproduced locally with XDG_CONFIG_HOME=/home/runner/.config; C1 clears it in the test. Suite 525 OK with and without XDG set. Push gate presented for 7ee973c.

## engine · Push gate · approved
2026-10-28T04:59:13Z
Owner approved; pushed head 548a5ec to #232.
