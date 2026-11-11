---
bump: patch
---
- Claude Code's paths follow `CLAUDE_CONFIG_DIR` when it holds an absolute path, `.claude.json` included, for `status`, `apply`, `doctor` and `uninstall`; unset, empty or relative, `~/.claude` as before. `harnesses.toml` paths take `${VAR:-default}` for this (#132).
- Codex's paths follow `CODEX_HOME` the same way, `config.toml` included; default `~/.codex` (#133).
- OpenCode's paths follow `XDG_CONFIG_HOME` (`$XDG_CONFIG_HOME/opencode`); default `~/.config/opencode`. MCP servers go into an existing `opencode.jsonc` when there is no `opencode.json` (or brainrc's servers are already there), edited in place so its comments stay; `uninstall` checks both files (#134).
- When a harness's variable changes between applies, `apply` and `status` warn that brainrc's links and hooks stay in the old dir, `doctor` warns while they are there, and `uninstall` also cleans each harness's default dir. `doctor` warns when one of the three variables is set to a relative path, which brainrc ignores.
