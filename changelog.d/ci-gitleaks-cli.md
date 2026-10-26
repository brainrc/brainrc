---
bump: patch
---
- CI runs the pinned gitleaks CLI (8.24.3, checksum-verified) instead of `gitleaks-action`, which fails without a paid license now that the repo is owned by an organization. It scans the same commit range with the same flags.
