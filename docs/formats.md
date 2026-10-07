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

| | Claude Code | Codex | OpenCode | Gemini CLI | Cursor |
|---|---|---|---|---|---|
| Skills | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rules | ✅ CLAUDE.md | ✅ AGENTS.md | ✅ AGENTS.md | ✅ GEMINI.md | ❌ Settings UI only |
| Commands | ✅ | ✅ prompts | ✅ | ⏳ needs TOML adapter | ⏳ |
| Agents | ✅ subagents | ↪ role-switch fallback | ↪ fallback (adapter ⏳) | ↪ fallback | ↪ fallback |
| Guard hooks | ✅ | ❌ rules only | ❌ | ❌ | ❌ |
| MCP | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |

Harness paths change often. If one moves, update `harnesses.toml`.
