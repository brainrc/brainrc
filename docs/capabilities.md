# What reaches each tool

Skills reach every tool. The rest depends on what each tool can load.

## At a glance

| | Claude Code | Codex | OpenCode | Antigravity CLI | Cursor | GitHub Copilot | Devin Local | Kiro | Amp | Junie | Gemini CLI |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Skills | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rules | ✅ `CLAUDE.md` | ✅ `AGENTS.md` | ✅ `AGENTS.md` | ✅ `AGENTS.md` | ↪ [plugin](plugins.md#cursor) only | ✅ `copilot-instructions.md` | ✅ `AGENTS.md` | ✅ steering `AGENTS.md` | ✅ `AGENTS.md` | ✅ `AGENTS.md` | ✅ `GEMINI.md` |
| Commands | ✅ | ✅ prompts | ✅ | ➖ skills are its slash commands | ⏳ | ⏳ | ➖ skills are its slash commands | ➖ skills are its slash commands | ⏳ | ⏳ | ⏳ TOML only |
| Agents | ✅ subagents | ↪ role-switch fallback | ✅ subagents (rendered) | ↪ fallback | ↪ fallback | ↪ fallback | ↪ fallback | ↪ fallback | ↪ fallback | ✅ subagents | ↪ fallback |
| Guard hooks | ✅ allow, ask, deny | ❌ rules only | ✅ plugin, deny only | ⏳ rules only | ✅ shell and reads, deny only | ✅ shell and files, deny only | ✅ shell, files, MCP, deny only | ✅ shell, files, MCP, deny only | ⏳ plugin API only | ✅ allow, ask, deny | ✅ shell, files, MCP, deny only |
| MCP servers | ✅ | ✅ | ✅ | ⏳ | ⏳ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

✅ supported · ↪ partly, or another way · ⏳ not yet · ➖ not needed · ❌ not possible today

"Fallback" means the tool has no named subagents brainrc can write, so
[Gatework](gatework.md#harness-support) switches roles inside one session. GitHub Copilot covers the
Copilot CLI and VS Code's Copilot agent, which share `~/.copilot`. Devin Local is the agent in Devin
Desktop, which Windsurf became. Gemini CLI is off by default ([configuration](configuration.md)). The
guards in Copilot, Devin Local, Kiro, Junie and Gemini CLI follow each tool's hook docs and are
tested with payloads shaped like them, not yet in the live tools ([guardrails](guardrails.md)).

## Where each piece goes

One row per tool: where `apply` puts each kind of content, and what a repo's `brainrc.toml`
writes for it ([team setup](project.md)). A dash means that tool gets none of it. Paths are the
defaults; the variables in the last column move them ([configuration](configuration.md#environment-variables)).
This table is generated from [`harnesses.toml`](../harnesses.toml), and a test fails when the two
disagree. The table at the top is written by hand: when you change `harnesses.toml`, update it too.

<!-- BEGIN capability matrix: generated from harnesses.toml by `brainrc capabilities --write` -->
| Tool | Skills | Rules | Agents | Commands | Guard hooks | MCP servers | In a repo | Moves with |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Code | `~/.claude/skills` | `~/.claude/CLAUDE.md` | `~/.claude/agents` | `~/.claude/commands` | `~/.claude/settings.json`: PreToolUse, SessionStart | `~/.claude.json` | `.agents/skills/`, `AGENTS.md`, `.claude/skills/` (copy), `CLAUDE.md` (imports AGENTS.md) | `CLAUDE_CONFIG_DIR` |
| Codex | `~/.codex/skills` | `~/.codex/AGENTS.md` | — | `~/.codex/prompts` | `~/.codex/hooks.json`: PreToolUse | `~/.codex/config.toml` | `.agents/skills/`, `AGENTS.md` | `CODEX_HOME` |
| OpenCode | `~/.config/opencode/skills` | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/agents` (rendered) | `~/.config/opencode/command` | plugin `~/.config/opencode/plugins/brainrc-guard.js` | `~/.config/opencode/opencode.json` | `.agents/skills/`, `AGENTS.md` | `XDG_CONFIG_HOME` |
| Antigravity CLI | `~/.gemini/config/skills` | `~/.gemini/config/AGENTS.md` | — | — | `~/.gemini/config/hooks.json`: PreToolUse | — | `.agents/skills/`, `AGENTS.md` | — |
| Gemini CLI (off by default) | `~/.gemini/skills` | `~/.gemini/GEMINI.md` | — | — | `~/.gemini/settings.json`: BeforeTool | `~/.gemini/settings.json` | `.agents/skills/`, `AGENTS.md` | — |
| Cursor | `~/.cursor/skills` | — | — | — | `~/.cursor/hooks.json`: beforeReadFile, beforeShellExecution | — | `.agents/skills/`, `AGENTS.md` | — |
| GitHub Copilot (CLI, VS Code) | `~/.copilot/skills` | `~/.copilot/copilot-instructions.md` | — | — | `~/.copilot/hooks/brainrc.json`: preToolUse | `~/.copilot/mcp-config.json` | `.agents/skills/`, `AGENTS.md` | `COPILOT_HOME` |
| Devin Local (was Windsurf) | `~/.config/devin/skills` | `~/.config/devin/AGENTS.md` | — | — | `~/.config/devin/config.json`: PreToolUse | `~/.config/devin/mcp_config.json` | `.agents/skills/`, `AGENTS.md` | — |
| Kiro | `~/.kiro/skills` | `~/.kiro/steering/AGENTS.md` | — | — | `~/.kiro/hooks/brainrc.json`: PreToolUse | `~/.kiro/settings/mcp.json` | `.agents/skills/`, `AGENTS.md` | `KIRO_HOME` |
| Amp | `~/.config/amp/skills` | `~/.config/amp/AGENTS.md` | — | — | — | `~/.config/amp/settings.json` | `.agents/skills/`, `AGENTS.md` | — |
| JetBrains Junie | `~/.junie/skills` | `~/.junie/AGENTS.md` | `~/.junie/agents` | — | `~/.junie/config.json`: PreToolUse | `~/.junie/mcp/mcp.json` | `.agents/skills/`, `AGENTS.md` | — |
<!-- END capability matrix -->

What the tables can't show:

- **Rules** reach Cursor only through its [plugin](plugins.md#cursor), because Cursor keeps its
  user rules in its Settings, not in a file.
- **Agents**: a tool with no agents path gets no agents from `apply`. OpenCode can't read Claude
  Code's agent format (a `tools: Read, Grep` line makes its whole config invalid), so `apply` links
  copies rendered to `~/.config/brainrc/opencode/agents/`. Each copy is a subagent denied every
  tool the agent lacks; its `model` is dropped, so it uses its caller's model, and `mcp__*` tools
  aren't mapped.
- **Guard hooks**: Claude Code can allow, ask or deny; OpenCode's plugin and Cursor's hooks can
  only deny, so whatever would ask is blocked ([guardrails](guardrails.md#gaps-by-tool)). Codex
  and Antigravity get the rules alone.
- **Off by default**: Gemini CLI was replaced by Antigravity CLI. Enable it in
  [`harnesses.local.toml`](configuration.md#harnesseslocaltoml) if your account still runs it. In
  a repo, an off-by-default tool gets files only when `brainrc.toml` names it in `harnesses`.
- **Antigravity CLI's paths** (`~/.gemini/config/`) come from its changelog and user reports, not
  a live run.

Tool paths change often. To move a tool, edit `harnesses.toml`, then run
`python3 scripts/brainrc.py capabilities --write`. To add one, write its adapter
([tool adapters](adapters.md)).
