---
bump: patch
---
- spec-agent `watch` now handles a merged or closed PR: a merged one is verified at the merge commit in a detached worktree (`pass`, `regression`, or `unverified`, with a suggested follow-up on regression), a closed one ends as `abandoned`, and `retro.md` gains an `## After delivery` section. `retro_report.py` adds Outcome, Post-merge, Time to merge, Review rounds, and CI failures per run, plus average time to merge and merged, abandoned, and regression counts; `--json` is `schema_version` 2.
