---
bump: patch
---
- Claude Code's paths follow `CLAUDE_CONFIG_DIR` when it holds an absolute path, `.claude.json` included, for `status`, `apply`, `doctor` and `uninstall`; unset, empty or relative, `~/.claude` as before. `harnesses.toml` paths take `${VAR:-default}` for this (#132).
- Codex's paths follow `CODEX_HOME` the same way, `config.toml` included; default `~/.codex` (#133).
- OpenCode's paths follow `XDG_CONFIG_HOME` (`$XDG_CONFIG_HOME/opencode`); default `~/.config/opencode`. MCP servers go into an existing `opencode.jsonc` when there is no `opencode.json`, edited in place so its comments stay (#134).
