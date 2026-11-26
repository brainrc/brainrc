# brainrc

brainrc installs one set of AI coding-agent config into **Claude Code, Codex CLI, OpenCode,
Antigravity CLI, Cursor, GitHub Copilot, Devin Local (Windsurf), Kiro, Amp and Junie**. You keep
your rules, skills, agents, guard hooks and MCP servers as plain files in git, and `brainrc apply` writes each piece where each tool looks for it.

```bash
uvx brainrc status          # preview: lists what apply would write, writes nothing
uv tool install brainrc     # or: pipx install brainrc
brainrc apply               # write it
```

## What you get

- **Rules** every session loads, rendered into each tool's instructions file (`~/.claude/CLAUDE.md`,
  `~/.codex/AGENTS.md`, ...).
- **Guard hooks** that ask before risky commands (`git push`, `terraform apply`, `kubectl delete`,
  ...) and block secrets from being written ([guardrails](guardrails.md)).
- **Gatework**, the default pack: skills and agents that take a ticket to a reviewed pull request,
  with you approving the spec, the plan and the push ([Gatework](gatework.md)).
- **Your own packs**: a folder or git repo of your rules and skills, layered on top
  ([packs](packs.md)).
- **A lockfile** that pins every pack to a commit and every file to a hash, so a team's repo gets
  the same agent files on every machine and in CI ([team setup](project.md)).

brainrc never overwrites a file it didn't write. It merges into your settings files and keeps a
backup.

## Where to start

| You want to | Read |
|---|---|
| Install it | [Install](install.md) |
| Try it end to end in ten minutes | [Getting started](getting-started.md) |
| Learn the words (pack, harness, profile, lockfile) | [Concepts](concepts.md) |
| Add your own rules and skills | [Packs](packs.md), then [your first pack](tutorial.md) |
| Give a repo's agents the same setup on every machine | [Team setup](project.md) |
| Look up a command or a config file | [Commands](commands.md), [configuration](configuration.md) |
| Fix something | [Troubleshooting](troubleshooting.md) |

The source is [github.com/brainrc/brainrc](https://github.com/brainrc/brainrc). Each release has
its own version of this site; the version menu at the top switches between them.
