# Campaign gh:241 · Epic E23: Unattended runs (one-shot and planning)

## 2026-10-30T01:53:17Z · intake (dry run)
- Members: gh:242, gh:243, gh:244, gh:245, gh:255, gh:256 (sub-issue order). All open, unassigned. None skipped.
- Shape: ordered (`--shape ordered`; members differ).
- Dependencies: MCP only, so the body fallback was used. No child has a `Depends on #N` line; #256's "Builds on #255" doesn't match the pattern. Source `none`: epic order.
- Order: 242, 243, 244, 245, 255, 256. No cycle, no out-of-epic link.
- `--dry-run`: stops at the Campaign gate.

## engine · Campaign gate · presented
2026-10-30T01:53:17Z
⛔ Campaign gate: campaign-241-unattended-runs (dry run)
Summary: ordered shape, 6 children in epic order (source none). Each child gets its own Spec and Plan gates; child N branches from child N-1.
Decide: shape and order.
Artifacts: specs/campaign-241-unattended-runs/campaign.json

## owner · Campaign gate · approved
2026-10-30T02:46:42Z
Owner: approve, with #255 first. #255 moved to the top of the epic's sub-issues. #242 and #256 got `Depends on #255` lines, and the "N of 6" labels were renumbered. Source `body`. Order: 255, 242, 243, 244, 245, 256.

- Child 1 gh:255 started: specs/255-run-worktrees/ on branch 255-run-worktrees.

## 2026-10-30T03:45:17Z · child 1 gh:255 verified
- Drafts ready (specs/255-run-worktrees/pr-body.md). Waits for the stack Deliver gate, unless the owner ships it on its own.

## 2026-10-30T04:12:21Z · gh:255 delivered on its own
- Owner: "Ship #255 now". Ready PR, base main. Spec change accepted. Child 2 gh:242 waits for the merge, then branches from main.

## 2026-10-30T04:27:34Z · gh:255 merged (#257, v0.5.2)
- Post-merge verify passed. Child 2 gh:242 is released; it waits for the owner's go and will branch from main, carrying the 255 records.

## 2026-10-30T04:28:30Z · child 2 gh:242 started
- First run in its own worktree (#255): ~/.brainrc-worktrees/brainrc/242-oneshot, branch 242-oneshot from main (after #257 merged). Carries the 255 records.

## 2026-10-31T15:42:25Z · child 2 gh:242 delivered
- Ready PR, base main, from the first run in its own worktree. Carries #255's records.

## 2026-10-31T15:57:02Z · gh:242 merged (#258, v0.5.3)
- Post-merge verify passed. Child 3 gh:243 waits for the owner's go.

## 2026-10-31T16:08:20Z · child 3 gh:243 started (--oneshot)
- Owner asked to oneshot it. Worktree ~/.brainrc-worktrees/brainrc/243-planning-mode.
