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
model: sonnet             # optional: haiku | sonnet | opus | inherit
---
System prompt...
```

spec-agent reads these files through `skills/spec-agent/roles`, a symlink to `../../agents`.
Keep it a symlink: `validate` fails otherwise ([Platforms](../README.md#platforms)).

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

## Packs: `pack.toml`

A separate repo with the same layout plus a `pack.toml`, layered on top of this one per
machine. Format and extension points: [packs.md](packs.md).

## Harness support

| | Claude Code | Codex | OpenCode | Antigravity CLI | Cursor |
|---|---|---|---|---|---|
| Skills | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rules | ✅ CLAUDE.md | ✅ AGENTS.md | ✅ AGENTS.md | ✅ AGENTS.md | ❌ Settings UI only |
| Commands | ✅ | ✅ prompts | ✅ | ➖ none: skills are its slash commands | ⏳ |
| Agents | ✅ subagents | ↪ role-switch fallback | ✅ subagents (rendered) | ↪ fallback | ↪ fallback |
| Guard hooks | ✅ | ❌ rules only | ✅ plugin, deny only | ❌ | ❌ |
| MCP | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |

OpenCode can't read Claude's agent frontmatter (a `tools: Read, Grep` string makes its whole config
invalid), so `apply` links copies rendered to `$AICFG_HOME/opencode/agents/`
(`agents_format = "opencode"` in `harnesses.toml`). Each copy has `mode: subagent` and a `deny` for
every tool the agent lacks; tools it has follow your own OpenCode permissions. Lossy: `model` is
dropped (the subagent uses its caller's model) and `mcp__*` tools aren't mapped.

Antigravity CLI paths (`~/.gemini/config/`) come from its changelog and user reports, not a live
run. It can also install ai-config as a plugin ([README](../README.md#claude-code-plugin-no-clone)).

Harness paths change often. If one moves, update `harnesses.toml`.
