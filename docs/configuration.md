# Configuration

Everything you set up for one machine lives in a few small TOML files that git never sees. A
repo's shared setup is different: it lives in `brainrc.toml` at the repo root ([team setup](project.md)).

## Where the files live

| You run brainrc | Local files go in |
|---|---|
| as an installed command (uv, pipx, Homebrew) | `~/.config/brainrc/` |
| from a clone | the clone's root (git ignores them) |

`~/.config/brainrc/` is brainrc's own folder, the **settings home**. Set `BRAINRC_HOME` to move it.
Whichever way you run brainrc, it renders the rules there, keeps the lock there and fetches git
packs into it.

| File | What it sets |
|---|---|
| `harnesses.local.toml` | which tools brainrc manages, and their paths |
| `packs.local.toml` | which packs this machine adds, or turns off |
| `brainrc.local.toml` | the profile, items to leave out, and this machine's pack settings |
| `rules/*.local.md` | rules for this machine only, loaded after all the others |

`brainrc init` writes the first three for you. Every file is optional.

## harnesses.local.toml

brainrc manages a tool when its folder exists (`~/.claude`, `~/.codex`, `~/.config/opencode`,
`~/.gemini/config`, `~/.cursor`) and skips it otherwise. This file overrides that, one table per
tool:

```toml
[cursor]
enabled = false        # leave Cursor alone, even though it's installed

[opencode]
enabled = true         # manage OpenCode before its folder exists
```

The table names are `claude`, `codex`, `opencode`, `antigravity`, `cursor`, `copilot` (the Copilot
CLI and VS Code's Copilot agent), `devin` (Devin Local, which Windsurf became), `kiro`, `amp`,
`junie`, and `gemini` (Gemini CLI, off by default: Google ended it for individual accounts in June
2026, and it shares `~/.gemini` with Antigravity CLI). A table can also change any path from
[`harnesses.toml`](../harnesses.toml), such as `skills` or `instructions`, though the variables below
are usually the better way.

## packs.local.toml

One table per pack, by a `path` on disk or a `git` URL:

```toml
[acme]
path = "~/src/acme-ai-pack"      # ~ and $VARS expand; a relative path is relative to this file

[team]
git = "git@github.com:acme/team-ai-pack.git"
ref = "v1.2.0"                   # a tag, branch or commit; default: the remote's default branch

[gatework]
enabled = false                  # turn off the default pack
```

| Key | Meaning |
|---|---|
| `path` | the pack's folder |
| `git` | a URL to fetch instead; private repos use your git credentials |
| `ref` | with `git`: what to fetch |
| `subdir` | with `git`: the folder of the repo that is the pack, for a repo that holds several ([packs](packs.md#packs-from-one-repo)) |
| `enabled` | `false` removes the pack's items on the next `apply` |
| `run_validator` | `true` lets a pack's own `validator.py` run ([packs](packs.md#validator-plugins)) |
| `description` | a note for people; ignored |

[Packs](packs.md) has the rest: how git packs are pinned, and how to point Gatework at a clone.

## brainrc.local.toml

How much this machine installs:

```toml
profile = "recommended"
exclude = ["gatework:skills/brainrc-aws", "gatework:agents/brainrc-infra-*"]
```

| `profile` | Installs |
|---|---|
| `minimal` | rules only |
| `recommended` | rules, skills, agents, commands and hooks |
| `full` (the default) | all of that, plus the MCP servers packs define |

`exclude` drops single items. A pattern matches an item's path in its pack (`skills/brainrc-aws`)
or that path after the pack's name (`gatework:skills/brainrc-aws`), and `*` and `?` work.
`brainrc init --profile <name>` or `--starter <name>` writes this file. `apply` removes what a
profile or pattern drops; `validate` still checks everything.

`[extensions.<namespace>]` holds this machine's settings for the pack that owns the namespace,
in the same form as a pack's [extensions](packs.md#extensions) table. That pack checks it on
`apply` and `doctor`, and `extensions.md` lists it after every pack's, under "This machine". A
namespace no enabled pack reads is a warning.

```toml
[extensions.gatework]
deliver_checks = ["Load test signed off"]
```

## Local rules

Files named `rules/NN-<topic>.local.md` in the settings home (or the clone) are added after every
other rule, under a note that they refine the rules above. They are plain markdown. Run `apply`
after each change.

## Environment variables

| Variable | Effect |
|---|---|
| `BRAINRC_HOME` | moves the settings home (default `~/.config/brainrc`) |
| `XDG_CONFIG_HOME` | when set to an absolute path, the settings home is `$XDG_CONFIG_HOME/brainrc`, and OpenCode's files are under `$XDG_CONFIG_HOME/opencode` |
| `CLAUDE_CONFIG_DIR` | moves Claude Code's files, `.claude.json` included |
| `CODEX_HOME` | moves Codex's files |

brainrc reads a tool's variable the way the tool does: an absolute path moves the files, and an
unset, empty or relative one means the default. So run brainrc with the same environment as the
tool. If a variable changes between two `apply` runs, brainrc's links stay in the old folder;
`apply` and `doctor` warn about it, and `uninstall` cleans both.

## Files brainrc keeps in the settings home

You don't edit these, but it helps to know what they are:

| File | What it is |
|---|---|
| `instructions.md` | the rendered rules every tool's instructions file links to |
| `extensions.md` | what packs add to Gatework, rendered for it to read |
| `brainrc.lock` | this machine's lock: pack commits, file hashes and permissions |
| `packs/` | git packs `apply` fetched |
| `hooks/` | a copy of the guard hooks, which tools run from here |
| `harnesses.json` | which tools and sources `apply` used, so `uninstall` works after a move |
| `mcp-owned.json`, `mcp-pins.json` | the MCP servers brainrc wrote, and their pinned tools |
