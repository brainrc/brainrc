---
bump: patch
---
- spec-agent parallel waves, from the first subagent-mode run of sandbox ticket 003
  (`docs/e2e-runs.md`): wave dispatch passes the worktree as `Project root` plus a `Worktree:`
  line, since subagent tools may not take a working directory; wave metrics count first attempts
  only, so a blocked retry no longer drops `task_minutes` and `wall_minutes`. Refs #25.
- Sandbox ticket 003 and its eval case say the ticket sizes `small` and needs `resize standard`
  to reach a wave; the case also requires the wave timings.
- `evals.py`: a `state` check can test that a field is `present`.
