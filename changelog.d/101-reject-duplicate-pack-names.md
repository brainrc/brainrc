---
bump: patch
---
- `validate`, `status`, `apply`, and `doctor` refuse two enabled packs with the same `name`, naming both `packs.toml` keys, and a pack named `core`. Before, the two shared one hooks dir and `apply` never settled (gh:101).
