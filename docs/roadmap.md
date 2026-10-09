# Roadmap

Shipped work is in the [CHANGELOG](../CHANGELOG.md).

Next:
- [ ] **E2E runs**: sandbox ticket in Claude Code, then Codex/OpenCode fallback; record retros.
- [ ] **Hooks for other tools** where pre-execution hooks exist (port `guard_outward`/`guard_secrets`).
- [ ] **MCP registry sync**: render `mcp/servers.toml` into each tool's config (merge, like settings).
- [ ] **Living specs** (OpenSpec-style): archive completed specs into per-domain `specs/` truth with deltas.
- [ ] **Metrics rollup**: `scripts/retro_report.py` aggregating `retro.md`/`state.json` across projects, plus ccusage cost.
- [ ] **Native packages for every harness** ([#50](https://github.com/bxker/ai-config/issues/50)): install core and packs without a clone; per-harness findings and order in [harness-packages.md](harness-packages.md).
