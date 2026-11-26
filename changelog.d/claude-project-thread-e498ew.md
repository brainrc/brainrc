---
bump: patch
---
- Cursor, OpenCode, Codex and Antigravity enforce packs' `[[guard.deny]]` and `[[guard.ask]]` rules
  under each pack's `[scope]`, judged where the command runs, by running core's Claude Code guards.
  A pack's deny wins over any ask. Where a tool can't ask (Cursor's shell hook, OpenCode, Codex),
  a pack's ask blocks the call and tells the model to ask you to run it (#155, #156).
- Codex gets core's guards through its PreToolUse hooks in `$CODEX_HOME/hooks.json`, for shell
  commands, `apply_patch` (checked for secrets as a write) and MCP calls. Codex asks you to trust
  new hooks once in `/hooks` (#157).
- Antigravity gets core's guards on `run_command` through its hooks in
  `~/.gemini/config/hooks.json`, under the name `brainrc`. A pack's ask is a prompt there.
  `harnesses.toml` takes `settings_format = "antigravity"` for that file's shape (#158).
- **[pack contract]** A `[[guard.deny]]` can set `path` or `host` in place of `match` or `tool`.
  `apply` compiles them into Claude Code's sandbox settings (`sandbox.filesystem.denyRead` and
  `denyWrite`, `sandbox.network.deniedDomains`), which the OS enforces on every Bash command, and
  owns the entries it adds as it does permissions. These rules are deny-only and apply everywhere,
  so a scoped pack gives each `scope = {}` (#322).
