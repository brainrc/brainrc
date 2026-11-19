# Canonical formats

The file formats a pack (and brainrc itself) uses. Each is the most widely adopted format for
its kind, so most tools read it as is. brainrc translates only where a tool needs another shape:
OpenCode's agents, and the OpenCode and Cursor guard hooks.

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
relative paths from SKILL.md. A connector skill declares its config under `metadata` as
`brainrc-config` ([packs.md](packs.md#connector-config)).

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

Gatework reads its role files through `skills/brainrc-gatework/roles`, a symlink to `../../agents`.
Keep it a symlink: `validate` fails otherwise ([platforms](install.md#platforms)).

## Commands: `commands/<name>.md`

For packs. Gatework ships its slash commands as user-invoked skills instead
(`disable-model-invocation: true` and `argument-hint` in `SKILL.md`), because Codex skips commands
that use `$ARGUMENTS`; a pack that targets Codex should do the same (`brainrc new command <name>
--as-skill` writes that form).

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
(`mcp`; `opencode.jsonc` when only that exists, edited in place so its comments stay). Each
moves with its harness's variable ([configuration](configuration.md#environment-variables)). `env_from` becomes a reference the harness expands when it starts the server
(`${NAME}`, `env_vars`, `{env:NAME}`), so no value is written anywhere; `validate` rejects an
`env` table. Only servers brainrc wrote are replaced or removed (tracked in
`$BRAINRC_HOME/mcp-owned.json`). A server you defined yourself under the same name is reported as a
conflict and left alone. Claude Code rewrites `~/.claude.json` while it runs, so apply MCP changes
with it closed. Cursor and Antigravity aren't supported yet.

`brainrc pin-mcp` records a hash of each stdio server's tool definitions, and a Claude Code
SessionStart hook warns when one changes ([guardrails](guardrails.md#claude-code-hooks)).

## Packs: `pack.toml`

A folder or repo with this layout plus a `pack.toml`: [packs](packs.md#packtoml).

`pack.toml`, `mcp/servers.toml` and `harnesses.toml` have JSON Schemas in [`schemas/`](schemas.md),
for editor completion ([packs.md](packs.md#editor-completion)).

## Project manifest and lock: `brainrc.toml`, `brainrc.lock`

A repo's own packs and the lock that pins them: [team setup](project.md), with JSON Schemas in
[`schemas/`](schemas.md).

## Harness support

Which of these formats each tool loads, and where: [what reaches each tool](capabilities.md).
