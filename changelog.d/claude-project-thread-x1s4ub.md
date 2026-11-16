---
bump: patch
---
- Install-time check: a Homebrew route over its 90-second limit is now a warning (a `WARN` line, a
  GitHub Actions `::warning::` annotation) instead of a failure, so a slow runner no longer turns
  `main` red; a Homebrew install that breaks, or a status that doesn't run, still fails, and the
  other routes still fail over 60 seconds. Each route's result also goes to the job's step summary.
