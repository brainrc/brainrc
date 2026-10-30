# Log: 242-oneshot

## engine · intake · done
2026-10-30T04:28:30Z
Campaign gh:241, child 2 of 6. The first run in its own worktree (#255): /home/user/.brainrc-worktrees/brainrc/242-oneshot, opened with `run_worktree.py open --base origin/main`. The owner's checkout stays on 255-run-worktrees, untouched. Merged in 255-run-worktrees to carry #255's post-merge records. Size: standard for now; the spec stage may resize it. Mode subagent. Domains: none (markdown engine docs plus evals). Targets: offline only.

## analyst · spec · done
2026-10-30T04:29:56Z
11 ACs and 8 open questions with defaults. The analyst wrote size "medium", which is not a tier; the engine set `standard`. living_specs check: exit 0 (run-lifecycle, campaign-mode).

## engine · Spec gate · presented
2026-10-30T04:29:56Z

## owner · Spec gate · approved
2026-10-30T04:34:52Z

## architect · plan · done
2026-10-30T04:38:16Z
6 tasks in 5 waves (T1; T2 alone, review each; T3+T4; T5; T6). Evals grade a new `pr_draft` field. Callouts: additive internal fields and evals.py campaign options.

## engine · Plan gate · presented
2026-10-30T04:38:16Z

## owner · Plan gate · approved
2026-10-30T13:38:20Z
Owner: "Go", with the engine defaults: `bump: patch` (not minor, since --oneshot is additive) and no split. The plan.md bump was changed after approval as a wording-only fix.

## implementer · T1 · done
6 of 7 new tests red first; tests/test_evals 87 OK; suite 625 OK. Committed. docs/evals.md is left to T6.
