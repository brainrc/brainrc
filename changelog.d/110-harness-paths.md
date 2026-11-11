---
bump: patch
---
- Claude Code's paths follow `CLAUDE_CONFIG_DIR` when it holds an absolute path, `.claude.json` included, for `status`, `apply`, `doctor` and `uninstall`; unset, empty or relative, `~/.claude` as before. `harnesses.toml` paths take `${VAR:-default}` for this (#132).
