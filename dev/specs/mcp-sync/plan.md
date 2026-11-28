# Plan: MCP registry sync

Spec: approved (Cursor: A, left out) · Mode: inline · Domains: scripting (Python tooling)

| Task | What | Files | Criteria |
|---|---|---|---|
| T1 | Tests first (red): registry checks, pack rules, three adapters, merge rules, apply/doctor wiring | `tests/test_mcp.py` | AC1–AC4 |
| T2 | `aicfg/mcp.py`: load each source's `mcp/servers.toml`, `check_servers` for `validate` (keys, command/url, env names, harness names, pack prefix, duplicates); `mcp` key needs an adapter | `aicfg/mcp.py`, `aicfg/validate.py` | AC1, AC2 |
| T3 | Adapters (claude, opencode JSON; codex marked TOML block), ownership in `$AICFG_HOME/mcp-owned.json`, conflicts skipped, backup + atomic write | `aicfg/mcp.py` | AC3 |
| T4 | Wire into `status`/`apply` and `doctor`; `mcp` keys in `harnesses.toml`; re-exports | `aicfg/cli.py`, `aicfg/doctor.py`, `aicfg/__init__.py`, `harnesses.toml` | AC3 |
| T5 | Real CLIs load the generated files (`claude`/`codex`/`opencode mcp list`); baseline transcript unchanged with the empty registry | none (evidence in `verify.md`) | AC4 |
| T6 | Docs and release 0.3.27 | README, `docs/*.md`, `mcp/servers.toml`, CHANGELOG, VERSION | AC5 |

Risks: `~/.claude.json` is rewritten by a running Claude Code, so apply writes only when something
changed, atomically, after a backup; docs say to apply MCP changes with Claude closed. Lost
ownership state: an entry equal to what aicfg would write is adopted, not reported as a conflict.
