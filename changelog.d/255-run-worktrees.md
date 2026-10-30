---
bump: patch
---
- spec-agent runs now work in their own git worktree at `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`, so your checkout is never touched. A run refuses to start when your checkout is on the run's branch.
- `/spec-resume` and `/spec-status` locate runs through `state.worktree`; resume recreates a missing worktree from `state.branch`. With no usable active-run pointer, `active_run.py read` also scans every branch worktree.
