# What reaches each tool

One row per tool brainrc manages: where `apply` puts each kind of content, and what a repo's
`brainrc.toml` writes for it ([project.md](project.md)). A dash means that tool gets none of it.
Paths are the defaults; the variables in the last column move them
([install](install.md)). The table is generated from [`harnesses.toml`](../harnesses.toml), so
it changes only when that file does, and a test fails when the two disagree.

<!-- BEGIN capability matrix: generated from harnesses.toml by `brainrc capabilities --write` -->
| Tool | Skills | Rules | Agents | Commands | Guard hooks | MCP servers | In a repo | Moves with |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/skills` | `~/.claude/CLAUDE.md` | `~/.claude/agents` | `~/.claude/commands` | `~/.claude/settings.json`: PreToolUse, SessionStart | `~/.claude.json` | `.claude/skills/` (copy), `CLAUDE.md` (imports AGENTS.md) | `CLAUDE_CONFIG_DIR` |
| Codex | `~/.codex/skills` | `~/.codex/AGENTS.md` | — | `~/.codex/prompts` | — | `~/.codex/config.toml` | `.agents/skills/`, `AGENTS.md` | `CODEX_HOME` |
| OpenCode | `~/.config/opencode/skills` | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/agents` (rendered) | `~/.config/opencode/command` | plugin `~/.config/opencode/plugins/brainrc-guard.js` | `~/.config/opencode/opencode.json` | `.agents/skills/`, `AGENTS.md` | `XDG_CONFIG_HOME` |
| Antigravity CLI | `~/.gemini/config/skills` | `~/.gemini/config/AGENTS.md` | — | — | — | — | `.agents/skills/`, `AGENTS.md` | — |
| Gemini CLI (off by default) | `~/.gemini/skills` | `~/.gemini/GEMINI.md` | — | — | — | — | — | — |
| Cursor | `~/.cursor/skills` | — | — | — | `~/.cursor/hooks.json`: beforeReadFile, beforeShellExecution | — | `.agents/skills/`, `AGENTS.md` | — |
<!-- END capability matrix -->

What the table can't show:

- **Rules** arrive in Cursor only through its plugin (`.cursor-plugin/`), because Cursor keeps its
  user rules in the Settings UI, not a file ([formats](formats.md#harness-support)).
- **Agents**: a tool with no agents path gets no agents from `apply`. OpenCode's copies are
  rendered to its own format, which drops `model` ([formats](formats.md#harness-support)).
- **Guard hooks**: Claude Code can allow, ask or deny; OpenCode's plugin and Cursor's hooks deny
  only ([guardrails](guardrails.md)). Codex and Antigravity get the rules alone.
- **Off by default**: Gemini CLI was replaced by Antigravity CLI. Enable it in
  `harnesses.local.toml` if your account still runs it.

To add or move a tool, edit `harnesses.toml`, then run `python3 scripts/brainrc.py capabilities --write`.
