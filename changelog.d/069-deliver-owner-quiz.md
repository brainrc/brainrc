---
bump: patch
---
- spec-agent: the Deliver gate now opens only after the run's owner passes an Understand quiz.
  A new read-only `examiner` role writes 1–5 free-text questions from the spec, plan, and diff
  (plus one per risk trigger touched). The engine grades each answer against the diff and
  explains and re-asks until every question is understood. No size or unattended run skips it.
  The questions go into the PR body, and `metrics.understanding` is recorded in state and the
  retro.
- evals: a `state` check can require `min = <n>`. Sandbox cases 001 and 003 now require
  `metrics.understanding.asked` ≥ 1.
