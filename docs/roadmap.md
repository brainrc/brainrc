# Roadmap

Shipped work is in the [CHANGELOG](../CHANGELOG.md).

Next, in order:
- [ ] **E2E: Codex/OpenCode fallback**: sandbox tickets 001 and 002 in fallback mode, graded with `evals.py check`; record in [e2e-runs.md](e2e-runs.md).
- [ ] **Hooks for other tools** where pre-execution hooks exist (port `guard_outward`/`guard_secrets`; OpenCode and Cursor done, deny only).
- [ ] **Native packages for every harness** ([#50](https://github.com/bxker/ai-config/issues/50)): install core and packs without a clone; per-harness findings and order in [harness-packages.md](harness-packages.md). Revisit splitting spec-agent into its own repo after this.

Done:
- [x] **Post-deliver `watch` stage**: follow the PR through CI, review, and merge, and feed the results into `state.json` and `retro.md` ([design](post-deliver.md)).
- [x] **Metrics rollup** ([#24](https://github.com/bxker/ai-config/issues/24)): `scripts/retro_report.py` rolls up `state.json` across runs, with optional ccusage period totals ([efficiency.md](efficiency.md#metrics-rollup)). Step one of post-deliver.
- [x] **E2E: subagent mode**: sandbox ticket 003 ran one parallel wave of named subagents and passed (resized to `standard`, [e2e-runs.md](e2e-runs.md)).
- [x] **E2E runs in Claude Code**: sandbox tickets 001 and 002 pass `evals.py check` (0.3.29, [e2e-runs.md](e2e-runs.md)).
- [x] **Releases**: changelog fragments, a release workflow, and `vX.Y.Z` tags (0.3.29).
- [x] **MCP registry sync**: `apply` merges `mcp/servers.toml` into Claude Code, Codex, and OpenCode (0.3.27); Cursor and Antigravity next.
- [x] **Living specs** (OpenSpec-style): runs apply requirement deltas to `specs/living/<area>.md` (0.3.28).
