# Log: 242-oneshot

## engine · intake · done
2026-10-30T04:28:30Z
Campaign gh:241, child 2 of 6. The first run in its own worktree (#255): ~/.brainrc-worktrees/brainrc/242-oneshot, opened with `run_worktree.py open --base origin/main`. The owner's checkout stays on 255-run-worktrees, untouched. Merged in 255-run-worktrees to carry #255's post-merge records. Size: standard for now; the spec stage may resize it. Mode subagent. Domains: none (markdown engine docs plus evals). Targets: offline only.

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

## security-reviewer · T2 · changes-requested
1 HIGH: a blocked draft PR pushes the branch on CRITICAL/HIGH, injection and secret stops. 2 MEDIUM (untrusted text in the blocked PR body and title; Callout defaults not checked after the fact; the additive contract default), 2 LOW.

## code-reviewer · T2 · done
No CRITICAL or HIGH. 4 MEDIUM (Auto vs oneshot precedence; --oneshot governs --auto missing; local-only on the blocked PR; campaign.md override), 5 LOW.

## owner · spec change · approved
2026-10-30T13:54:30Z
Owner: "Split the stops". Tainted stops (security finding, injection, secret) push nothing and open no PR, like --auto. Benign stops (retry budget, scope breach, spec gap, no safe Callout default) open a draft [blocked] PR with a fixed title phrase, never quoting untrusted text. Owner kept the additive contract default. The analyst revised AC3, AC4, AC8, the Constraints table and the 3 requirement blocks; living check exit 0. Plan T3 now has 3 tainted and 4 benign cases (added tickets 032 and 033, cases 028 and 029). T5's blocked child (secret) now opens no PR.

## engine · T2 attempt 2 (inline)
The container restarted twice and killed the attempt-2 subagent both times before it edited anything. The engine made the edits inline instead (fallback for this task only). The spec change and all review findings are applied, except the post-hoc check that Callout defaults held in the diff: that is a new requirement, so it goes to Follow-ups. Validate OK; suite OK. Committed 8eeda14 before the re-review so another restart cannot lose it.

## security-reviewer · T2-rereview · done
All earlier findings fixed; no CRITICAL or HIGH. 2 MEDIUM (unlisted stops not fail-closed; untrusted ticket title in the [blocked] title) and 3 LOW. All fixed by the engine as F1 (d2c8dbf).

## engine · spec change after approval (wording, listed at Deliver)
AC4 and the "Oneshot blocked PR" requirement: the title is now `[blocked] <ticket ref>: <fixed phrase>`, not `<ticket title>`. The owner's decision was that the title "uses a fixed phrase"; the ticket title is untrusted. living check exit 0. The Oneshot subsection is 17 lines, over the plan's 15-line cap.

## engine · implement · wave {T3, T4}
2026-10-30T18:20:14Z

## implementer · T3, T4 · done
Wave in nested task worktrees (`git -C <run worktree> worktree add`, the #255 rule). Both fences OK. Landed T3 85f4967 (7 stop cases), T4 c21be9d (4 flag cases). Suite OK; validate OK.

## implementer · T5 · done
3 campaign cases; suite 647 OK. Committed f8229d0.

## engine · T6 · done (inline)
README rows, docs/evals.md and the changelog fragment (`bump: patch`), done inline because of the container restarts. Validate OK; suite OK. Committed 4e8b9da. Next: batch review.

## code-reviewer · batch · changes-requested
2 HIGH: no AC8 benign-child case; AC10 resume untested. 6 MEDIUM: blocked-body regex too weak and ref ungraded; for-each-ref check cannot fail; `ready` passes when `pr_draft` is missing; stacked base allows main for every child; large-split campaign ref undocumented; 021 Callout coverage. 3 LOW. Fix tasks: F4 (campaign ref doc, inline), F3 (evals.py strictness), F2 (cases).

## implementer · F3, F2 · done
F3 58035a4: strict ready, strict_stack and min_members. F2 43a58b8: cases hardened, 030 and 031 added. The engine changed F2's min_members guess of 5 to 2, because ticket 028 does not fix the split size (noted for the PR body). Suite OK; validate OK.

## code-reviewer · fix-review · done
All batch findings fixed; no CRITICAL or HIGH. 2 MEDIUM and 2 LOW, fixed by the engine as F5 (478fdb3); the base test was red without the fix. Suite OK; validate OK.

## engine · verify
2026-10-31T05:17:20Z

## verifier · verify · done
2026-10-31T05:22:09Z
Suite 659 OK, plain and with XDG; validate and validate --pack OK; 16 cases parse. AC1-AC11 pass against fake runs or instruction text. Real --oneshot runs not run (need a model).

## doc-writer · document · done
pr-body.md and ticket-comment.md written. The engine fixed the fragment range (016–031) as wording. Living specs applied.

## engine · Deliver gate · presented
2026-10-31T05:23:54Z

## owner · Deliver gate · approved
2026-10-31T15:42:25Z
Owner: approve, ready PR. The ticket-ref blocked title is confirmed. Retro written before the PR opened.

## engine · deliver · done
2026-10-31T15:52:32Z
Pushed; ready PR #258 (base main); ticket comment posted on #242. PR body: two stale lines fixed (ticket comment now posted; fragment range already fixed). Records pushed right away, before any merge. Watching #258.

## engine · watch · done
2026-10-31T15:57:02Z
#258 merged (v0.5.3). Post-merge verify passed. Every pre-merge record reached main. Only this post-merge record is local; it rides along with child 3.
