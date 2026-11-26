---
bump: patch
---
- Each AI tool now has an adapter in `brainrc/adapters/`, one module per tool, behind a small
  Python interface: its agent and settings formats, how it spells an MCP server, the guard rules
  its sandbox takes, and its name. `harnesses.toml` stays the paths file, `harnesses.local.toml`
  overrides included, and `apply` writes the same files for Claude Code, Codex, OpenCode,
  Antigravity, Cursor and Gemini CLI as before (golden tests hold every one). A Python package can
  add a tool with no change to core, through one entry point in the `brainrc.adapters` group
  ([tool adapters](docs/adapters.md)) (#306).
