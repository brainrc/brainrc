---
bump: patch
---
- CI now runs local tripwires on every pull request and push to `main`, with the terms from the
  `TRIPWIRE_TERMS` repository secret, so changes made in cloud sessions or on github.com can't skip
  the check. The log names a match's file, line and term number, never the term. Without the secret
  the check skips with a notice, and fork PRs are checked on the merge to `main` (#344).
- `validate --local-tripwires FILE` reads the terms from FILE instead of `tripwires.local.toml`.
