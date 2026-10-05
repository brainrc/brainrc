# Roadmap

Shipped work is in the [CHANGELOG](../CHANGELOG.md).

Next:
- [ ] **E2E runs**: sandbox ticket in Claude Code, then Codex/OpenCode fallback; record retros.
- [ ] **OpenCode agent adapter**: render `agents/*.md` into OpenCode's agent format so it gets real subagents.
- [ ] **Hooks for other tools** where pre-execution hooks exist (port `guard_outward`/`guard_secrets`).
- [ ] **MCP registry sync**: render `mcp/servers.toml` into each tool's config (merge, like settings).
- [ ] **Gemini command adapter**: markdown commands → TOML.
- [ ] **Living specs** (OpenSpec-style): archive completed specs into per-domain `specs/` truth with deltas.
- [ ] **Metrics rollup**: `scripts/retro_report.py` aggregating `retro.md`/`state.json` across projects, plus ccusage cost.
- [ ] **Parallel tasks**: run independent tasks (disjoint `files`, no deps) concurrently in subagent mode.
- [ ] **Plugin packaging**: publish as a Claude Code plugin/marketplace.
