---
bump: patch
---
- The release workflow creates a GitHub Release for each `vX.Y.Z` tag, with that version's `CHANGELOG.md` section as its notes. It skips a release that already exists. `python3 scripts/aicfg.py release --notes X.Y.Z` prints those notes.
