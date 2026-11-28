---
bump: patch
---
- This repo's own Gatework records (run folders, living specs, campaigns) moved from `specs/` at
  the root to `dev/specs/`, and AGENTS.md names it as the repo's specs directory, so new runs write
  there too (#175). Gatework still writes `specs/<slug>/` in your project.
