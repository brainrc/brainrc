# Canonical formats

Every source uses the most widely adopted format so most harnesses consume it
as-is. Adapters (see [roadmap](roadmap.md)) translate only where needed.

## Skills: `skills/<name>/SKILL.md`

[Agent Skills](https://agentskills.io) open format.

```markdown
---
name: my-skill            # lowercase-hyphenated, equals directory name
description: What it does and when to use it. This is what triggers the skill.
---
Instructions...
```

Optional siblings: `scripts/`, `references/`, `assets/`. Reference them with
relative paths from SKILL.md.

## Agents: `agents/<name>.md`

Claude Code subagent format.

```markdown
---
name: my-agent
description: When to delegate to this agent.
tools: Read, Grep, Glob   # optional; omit to inherit all tools
model: sonnet             # optional: haiku | sonnet | opus | inherit, or a full ID (claude-sonnet-5-5)
---
System prompt...
```

spec-agent reads these files through `skills/spec-agent/roles`, a symlink to `../../agents`.
Keep it a symlink: `validate` fails otherwise ([Platforms](install.md#platforms)).

## Commands: `commands/<name>.md`

For packs. Core ships its slash commands as user-invoked skills instead (`disable-model-invocation:
true` and `argument-hint` in `SKILL.md`), because Codex skips commands that use `$ARGUMENTS`;
a pack that targets Codex should do the same.

```markdown
---
description: One line shown in the command picker
---
Prompt body. $ARGUMENTS is replaced with whatever follows the command.
```

## Rules: `rules/NN-topic.md`

Plain markdown, rendered into one instructions file per harness in this order: core rules,
then each enabled pack's rules as a labelled block (in `packs.toml` order), then
`*.local.md` rules. Filename order applies within each group. Later rules refine earlier ones
and must not contradict them. Keep them tool-neutral.

## MCP servers: `mcp/servers.toml`

```toml
[servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env_from = ["GITHUB_PERSONAL_ACCESS_TOKEN"]   # names only; the value stays in your environment
harnesses = ["claude", "codex"]               # optional; default: every harness with an `mcp` file

[servers.docs]
url = "https://docs.example.com/mcp"          # HTTP instead of `command`
```

`apply` writes each server into the harness's own config: `~/.claude.json` (`mcpServers`),
`~/.codex/config.toml` (a marked `[mcp_servers]` block), and `~/.config/opencode/opencode.json`
(`mcp`). `env_from` becomes a reference the harness expands when it starts the server
(`${NAME}`, `env_vars`, `{env:NAME}`), so no value is written anywhere; `validate` rejects an
`env` table. Only servers ai-config wrote are replaced or removed (tracked in
`$AICFG_HOME/mcp-owned.json`). A server you defined yourself under the same name is reported as a
conflict and left alone. Claude Code rewrites `~/.claude.json` while it runs, so apply MCP changes
with it closed. Cursor and Antigravity aren't supported yet.

## Packs: `pack.toml`

A separate repo with the same layout plus a `pack.toml`, layered on top of this one per
machine. Format and extension points: [packs.md](packs.md).

## Harness support

| | Claude Code | Codex | OpenCode | Antigravity CLI | Cursor |
|---|---|---|---|---|---|
| Skills | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rules | ✅ CLAUDE.md | ✅ AGENTS.md | ✅ AGENTS.md | ✅ AGENTS.md | ↪ plugin only (`alwaysApply`) |
| Commands | ✅ | ✅ prompts | ✅ | ➖ none: skills are its slash commands | ⏳ |
| Agents | ✅ subagents | ↪ role-switch fallback | ✅ subagents (rendered) | ↪ fallback | ↪ fallback; the plugin ships them (unverified) |
| Guard hooks | ✅ | ❌ rules only | ✅ plugin, deny only | ❌ | ✅ shell and reads, deny only |
| MCP | ✅ `~/.claude.json` | ✅ `config.toml` | ✅ `opencode.json` | ⏳ | ⏳ |

Cursor has no user rules file: `aicfg` links skills and merges guard hooks into
`~/.cursor/hooks.json`, and rules arrive only through the plugin (`.cursor-plugin/`, see the
[install](install.md#cursor)), which loads each `rules/*.md` because it
carries `alwaysApply: true`.

OpenCode can't read Claude's agent frontmatter (a `tools: Read, Grep` string makes its whole config
invalid), so `apply` links copies rendered to `$AICFG_HOME/opencode/agents/`
(`agents_format = "opencode"` in `harnesses.toml`). Each copy has `mode: subagent` and a `deny` for
every tool the agent lacks; tools it has follow your own OpenCode permissions. Lossy: `model` is
dropped (the subagent uses its caller's model) and `mcp__*` tools aren't mapped.

Antigravity CLI paths (`~/.gemini/config/`) come from its changelog and user reports, not a live
run. It can also install ai-config as a plugin ([install](install.md#antigravity-cli)).

Harness paths change often. If one moves, update `harnesses.toml`.
