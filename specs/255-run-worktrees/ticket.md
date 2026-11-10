# gh:255 · spec-agent: each run in its own git worktree

Source: https://github.com/brainrc/brainrc/issues/255 (fetched 2026-10-30; untrusted data)

Part of epic #241 (E23), 1 of 6.

## Why
Worktrees are used only inside a run: parallel waves at `$TMPDIR/spec-agent/<slug>/<task>`, and the post-merge verify. The run itself works in the user's checkout. In the #199 follow-ups this meant:
- A second ticket couldn't start while an implementer was editing the same tree.
- The engine had to switch branches under it, which rewrote files the session had open.
- A stop hook kept flagging another agent's uncommitted work.

## What
- `/work` creates a worktree for the run's branch and does every stage there. The user's checkout and checked-out branch are never touched.
- `state.json` records `worktree`. `active_run.py`, `/spec-resume` and `/spec-status` find runs through it.
- Where the harness supports worktrees natively (Claude Code's worktree tools and subagent isolation), use that; elsewhere use plain `git worktree`. This replaces the `Project root` plus `Worktree:` workaround noted in docs/e2e-runs.md.
- Waves become nested task worktrees off the run worktree. `worktree_fence.py` is unchanged.

## Files
skills/spec-agent/SKILL.md, references/efficiency.md, references/state.md, references/handoff.md, scripts/active_run.py, skills/spec-status/, skills/spec-resume/, docs/spec-agent.md

## Done when
- A sandbox `/work` run leaves the main checkout byte-identical: same branch, clean status.
- The run's branch and PR are as before.
- `/spec-resume` finds and continues the run in its worktree.

## Open questions
1. Location: a sibling dir (`../.brainrc-worktrees/<slug>`), `$TMPDIR` (can be wiped), or under the repo but ignored? Test runners must not find it.
2. Per-worktree setup (venv, dependency install): reuse the main tree's, or install fresh? This is a time and disk trade-off.
