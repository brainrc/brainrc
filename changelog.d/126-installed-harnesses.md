---
bump: patch
---
- `apply` only touches harnesses that are installed: a machine with just Claude Code gets only `~/.claude` changes, and `~/.codex`, `~/.cursor` and the rest are no longer created. A harness counts as installed when its config directory exists (a new optional `home` key in harnesses.toml sets which one). `status` and `apply` name the ones they skip; `enabled = true` in harnesses.local.toml manages one anyway. `apply` records the harnesses it manages, and the source roots it linked from, in `$BRAINRC_HOME/harnesses.json`. `doctor` no longer warns about a harness that isn't installed, since `apply` skips it.
