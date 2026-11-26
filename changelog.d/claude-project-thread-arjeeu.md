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
- `apply` now manages GitHub Copilot: the Copilot CLI and VS Code's Copilot agent share
  `~/.copilot` (`COPILOT_HOME`), which gets your skills, `copilot-instructions.md`, MCP servers and
  a `preToolUse` guard in its own hook file, `hooks/brainrc.json` (#307).
- Gemini CLI gets a `BeforeTool` guard and MCP servers in `~/.gemini/settings.json`. Google ended
  it for individual accounts in June 2026 (it goes on for Code Assist and paid API keys), so it
  stays off by default: `[gemini] enabled = true` in `harnesses.local.toml` turns it on (#308).
- `apply` now manages Devin Local, the agent in Devin Desktop, which Windsurf became:
  `~/.config/devin` gets your skills, `AGENTS.md`, MCP servers and a `PreToolUse` guard in
  `config.json` (#309).
- `apply` now manages Kiro (`~/.kiro`, `KIRO_HOME`): skills, an `AGENTS.md` in global steering,
  MCP servers and a `PreToolUse` guard in its own hook file, `hooks/brainrc.json` (#310).
- `apply` now manages Amp (`~/.config/amp`): skills, `AGENTS.md` and MCP servers under
  `amp.mcpServers`. Amp has no command hooks, so it gets no guard (#311).
- `apply` now manages JetBrains Junie (`~/.junie`): skills, subagents, `AGENTS.md`, MCP servers and
  a `PreToolUse` guard in `config.json` that can ask as well as deny (#312).
- Each new tool is managed only once its folder exists, and its guard is tested with payloads
  shaped like its docs, not yet in the live tool ([guardrails](docs/guardrails.md)).
- Uninstall takes both brainrc's hooks and its MCP servers out of a file that holds both, as Gemini
  CLI's `settings.json` does, and an installed adapter's own agent format is cleaned up like
  OpenCode's. A tool that is off no longer reports a conflict for a settings or MCP file brainrc
  can't parse when nothing of brainrc's is in it, such as a Gemini CLI `settings.json` with
  comments.
