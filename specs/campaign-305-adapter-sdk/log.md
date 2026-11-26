# Campaign gh:305 · adapter SDK and more tools (E31)

## 2026-11-26T16:05:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:305 --shape playbook --batch-size 3 --dry-run`, worked by hand: the
skill ships in brainrc/gatework, which isn't installed in the build environment.

- Members, all open on GitHub at the start: #306 (adapter interface), then #307 (Copilot and VS
  Code), #308 (Gemini CLI), #309 (Windsurf), #310 (Kiro), #311 (Amp), #312 (Junie).
- Shape: `playbook`, as the epic body names, batch size 3. #306 seeds the playbook; the six tool
  adapters follow in two batches of three, in build order.
- Delivery: one draft PR with one commit per child, since only one branch is pushable here.
- Starts from `main` at d1ffda5 (v0.8.31), after E10 (#387) and E11 (#388).

## engine · Campaign gate · approved
The coordinator's brief passes on the maintainer's decision, "No keep it python. And continue",
to the question of porting the guard evaluator to Go before E31: everything stays Python 3.11+,
stdlib only, with no seam for a port. Recorded as approved on that basis. Merging, tagging,
releasing and closing #305 stay with the maintainer.

## engine · gh:306 · Spec and Plan
- An adapter is a Python class (`brainrc/adapters/base.py`) that declares what a tool's content
  looks like: its agent format, where its settings file keeps hooks, how it spells an MCP server,
  which guard rules its sandbox takes, and its label. The defaults are Claude Code's, so an
  adapter overrides only what its tool does differently. Shipped tools keep their paths in
  `harnesses.toml`; an adapter from a package brings its own table in `paths`, through the
  `brainrc.adapters` entry point group, and `harnesses.local.toml` overrides it the same way.
- The tool branches move out of `plan.py` (rendered agents), `settings.py` (Antigravity's named
  entry), `opencode.py` (removed: its renderer is OpenCode's adapter), `mcp.py` (each tool's entry,
  Codex's TOML block, OpenCode's jsonc), `guard.py` (Claude Code's sandbox lists) and
  `capabilities.py` (labels). `agents_format` and `settings_format` still work and now name the
  adapter whose format to borrow.
- Goldens first: `tests/test_adapter_goldens.py` records every file and link `apply` writes in user
  scope (default tools, Gemini CLI turned on, every tool turned off again) and in project scope,
  committed before the move; the move leaves all four unchanged.
- Plan: `brainrc/adapters/` (new), `config.py`, `plan.py`, `settings.py`, `mcp.py`, `guard.py`,
  `capabilities.py`, `doctor.py`, `cli.py`, `uninstall.py`; `docs/adapters.md`; tests in
  `tests/test_adapters.py` and `tests/test_adapter_goldens.py`.
