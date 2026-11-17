# Plugins

Most tools can also install brainrc as a plugin, with no `brainrc` command. There are two plugins:

- **`brainrc`** (this repo): the guard hooks, and the rules where a tool's plugins can load them.
- **`gatework`** ([brainrc/gatework](https://github.com/brainrc/gatework)): Gatework's skills
  (`/brainrc-work` and the rest) and its agents.

Install both to get close to what `brainrc apply` installs.

## Plugins or the brainrc command?

| | Plugins | `brainrc` command |
|---|---|---|
| Skills and agents | yes, from `gatework` | yes |
| Guard hooks | Claude Code and Cursor | Claude Code, OpenCode and Cursor |
| Rules | Antigravity and Cursor only | every tool |
| Your own packs | no | yes |
| Lockfile, `check`, `audit` | no | yes |

**Use one, not both**, for each tool: together they load every skill and hook twice. `doctor`
warns when it sees both in Claude Code or Cursor ([fix](troubleshooting.md#every-skill-shows-up-twice-or-a-hook-runs-twice)).

## Claude Code

```text
/plugin marketplace add brainrc/brainrc
/plugin install brainrc@brainrc
/plugin marketplace add brainrc/gatework
/plugin install gatework@gatework
```

Plugin skills are named after their plugin, so Gatework's command is `/gatework:brainrc-work`.
Claude Code plugins can't load rules into every session: for the rules, copy `rules/*.md` from
this repo into your own `~/.claude/CLAUDE.md`.

## Codex

```text
codex plugin marketplace add brainrc/brainrc
codex plugin add brainrc@brainrc
codex plugin marketplace add brainrc/gatework
codex plugin add gatework@gatework
```

Codex gets Gatework's skills (call them by name, such as `brainrc-work`) and the agent files
Gatework reads. Codex plugins can't carry rules: copy `rules/*.md` into `~/.codex/AGENTS.md`, or
use the `brainrc` command. Whether Codex runs the `brainrc` plugin's guard hooks is not yet
verified ([research](harness-packages.md#codex)).

## Antigravity CLI

```text
agy plugin install https://github.com/brainrc/brainrc
agy plugin install https://github.com/brainrc/gatework
```

The first brings the rules, the second the skills. Antigravity has no place for agents in a plugin,
so Gatework reads its role files directly. Guard hooks aren't included yet: use agy's own
permission settings. This install was built from Antigravity's public docs and hasn't been run
end to end ([research](harness-packages.md#antigravity-cli)).

## Cursor

Cursor loads a local clone as a plugin:

```bash
git clone https://github.com/brainrc/brainrc ~/src/brainrc
git clone https://github.com/brainrc/gatework ~/src/gatework
ln -s ~/src/brainrc ~/.cursor/plugins/local/brainrc
ln -s ~/src/gatework ~/.cursor/plugins/local/gatework
```

The first brings the rules and the guard hooks for shell commands and file reads (they deny
instead of asking); the second brings the skills and agents. Cursor keeps its user rules in its
Settings, not in a file, so this plugin is the only way brainrc's rules reach Cursor. Built from
Cursor's official plugin repo and not yet run in a real Cursor ([research](harness-packages.md#cursor)).

## OpenCode

OpenCode plugins are JavaScript modules that can't ship skills or agents, so there is no
OpenCode plugin. Use the `brainrc` command.
