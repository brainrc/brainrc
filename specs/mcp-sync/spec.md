# Spec: apply syncs mcp/servers.toml into Claude Code, Codex, and OpenCode

Ticket: gh:21 (closes) · Size: standard (new module, three adapters, pack rules) · Status: draft

## Background (checked with the real CLIs here)
- **Claude Code 2.1.296**: user-scope servers live in `~/.claude.json` → `mcpServers.<name>`,
  `{"type": "stdio", "command", "args", "env"}` or `{"type": "http", "url"}` (what `claude mcp add
  --scope user` writes). A probe server under `claude mcp list` saw `${VAR}` in `env` expanded.
- **Codex 0.161.0**: `~/.codex/config.toml` → `[mcp_servers.<name>]` with `command`, `args`, or
  `url`. `env_vars = ["NAME"]` forwards a variable by name (`codex mcp get` shows it).
- **OpenCode 1.18.35**: `opencode.json` → `mcp.<name>`, `{"type": "local", "command": [...],
  "environment": {"NAME": "{env:NAME}"}, "enabled": true}` or `{"type": "remote", "url"}`. A probe
  under `opencode mcp list` connected and saw the variable substituted.
- Claude and OpenCode servers also inherit the parent environment; the references keep it explicit.

## Acceptance criteria
- **AC1 Registry.** `[servers.<name>]`: `command` + optional `args` (stdio) or `url` (HTTP);
  optional `env_from = ["NAME"]`, `harnesses = ["claude", ...]` (default: every harness with an
  `mcp` key). `validate` rejects unknown keys, both or neither of `command`/`url`, an `env` table
  (values would be secrets), and invalid variable names. Core's registry stays all commented out, so
  nothing changes for anyone until they add a server.
- **AC2 Packs.** A pack's `mcp/servers.toml` adds servers. Names must start with the pack's
  `prefix`; a name defined twice is an error.
- **AC3 Merge.** New harness key `mcp` (a file): `[claude] mcp = "~/.claude.json"`,
  `[codex] mcp = "~/.codex/config.toml"`, `[opencode] mcp = "~/.config/opencode/opencode.json"`.
  `apply` writes each server in that harness's format; env vars only as references (`${NAME}`,
  `env_vars`, `{env:NAME}`), never a value. JSON files: only the `mcpServers`/`mcp` entries ai-config
  wrote are replaced or removed, tracked in `$AICFG_HOME/mcp-owned.json`. Codex: a marked block
  in `config.toml` that aicfg rewrites. A server name the user already defined is never
  overwritten: it's reported as a conflict and skipped. Backups and atomic writes as for settings;
  `status` shows `MERGE … (mcp)`; `doctor` reports drift and conflicts; a disabled harness gets its
  servers removed. A key `mcp` on a harness without an adapter fails `validate`.
- **AC4 Tests**: foreign entries kept, stale owned entries removed, conflicts skipped, idempotent,
  no value written for `env_from`, Codex block round-trips through `tomllib`, pack prefix and
  collision errors, and empty registry writes nothing. Generated files load in the real CLIs
  (`claude mcp list`, `codex mcp list`, `opencode mcp list`).
- **AC5 Docs**: support table MCP row, `docs/formats.md` registry section, `docs/packs.md`,
  `mcp/servers.toml` header, roadmap, CHANGELOG, VERSION 0.3.27.

## Open choice
- **Cursor.** (A, recommended) Leave it out: `~/.cursor/mcp.json` and its `${env:NAME}` syntax
  can't be checked here, and a wrong reference would override the inherited value. (B) Add it now,
  unverified, tracked in #63.

## Not in this step
Antigravity (no verified config path), HTTP auth headers (`bearer_token_env_var` and the like),
project-scope `.mcp.json`, and per-server tool filters.
