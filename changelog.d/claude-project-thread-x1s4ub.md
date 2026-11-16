---
bump: patch
---
- Install-time check: a Homebrew route over its 90-second limit is now a warning (a `WARN` line, a
  GitHub Actions `::warning::` annotation) instead of a failure, so a slow runner no longer turns
  `main` red. It still fails over a 180-second ceiling, or when the install or the first `status`
  breaks; the other routes still fail over 60 seconds, and an explicit `--limit` is a hard limit
  for every route. Under GitHub Actions each route's result also goes to the job's step summary.
