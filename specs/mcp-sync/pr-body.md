## Summary
`aicfg apply` now syncs `mcp/servers.toml` into Claude Code, Codex, and OpenCode (closes #21).

- **Registry:** `[servers.<name>]` takes `command` + `args` (stdio) or `url` (HTTP), plus optional `env_from = ["NAME"]` and `harnesses = [...]`. `validate` checks it and rejects an `env` table, so values can't be committed.
- **Where servers go:**
  - Claude Code: `~/.claude.json` under `mcpServers`.
  - Codex: a marked `[mcp_servers]` block in `~/.codex/config.toml`.
  - OpenCode: `~/.config/opencode/opencode.json` under `mcp`.
  - Each comes from a new harness key, `mcp`.
- **Secrets stay out of files:** `env_from` is written as a reference each harness expands when it starts the server (`${NAME}`, `env_vars`, `{env:NAME}`), never as a value.
- **Your servers are safe:** only servers ai-config wrote are replaced or removed (tracked in `$AICFG_HOME/mcp-owned.json`). A server you defined under the same name is reported as `CONFLICT` and left alone. Every write is backed up first and atomic, as for settings.
- **Reporting:** `status` shows `MERGE … (mcp)`, `doctor` reports drift and conflicts, and a disabled harness loses its servers on the next `apply`.
- **Packs** may ship `mcp/servers.toml` (pack-contract addition); server names need the pack's prefix.
- **No change by default:** core's registry stays empty, so nothing happens until you add a server.
- **Not covered:** Cursor and Antigravity (formats can't be checked here), HTTP auth headers, and project-scope `.mcp.json`.
- `VERSION` 0.3.27.

## Acceptance criteria
- [x] AC1 registry format and validation
- [x] AC2 pack servers: prefix and collisions
- [x] AC3 merge into three harnesses, ownership, conflicts, doctor
- [x] AC4 tests and real CLIs
- [x] AC5 docs, CHANGELOG, VERSION

## Testing
- `python3 -m unittest discover -s tests` → OK (200, 17 new in `tests/test_mcp.py`).
- **Real CLIs**, after `apply` in a fake home with a probe server that records its environment:
  - Claude Code 2.1.296 (`claude mcp list`) and OpenCode 1.18.35 (`opencode mcp list`) both connected, and the probe received the variable.
  - Codex 0.161.0 (`codex mcp get`) lists the server with the variable forwarded; its CLI doesn't connect, so launching under Codex is unverified.
  - The secret value appears in none of the written files.
  - A server added afterwards with `claude mcp add` is kept, and removing the probe from the registry removes it from all three files.
- `validate` (core and pack) → OK. The checkout transcript matches main except for one new help line.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
