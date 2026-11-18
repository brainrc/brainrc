# brainrc

brainrc installs one set of AI coding-agent config (rules, skills, agents, guard hooks and MCP servers) into **Claude Code, Codex CLI, OpenCode, Antigravity CLI and Cursor** ([what reaches each tool](docs/capabilities.md), [the words these docs use](docs/concepts.md)).

You write your config once, as plain files in a git repo (a **pack**), and `brainrc apply` puts each
piece where each tool looks for it. It never overwrites a file it didn't write. Full docs:
[brainrc.github.io/brainrc](https://brainrc.github.io/brainrc/).

## Quickstart

Needs [uv](https://docs.astral.sh/uv/getting-started/installation/) and git. uv fetches a Python
if you have none.

```bash
uvx brainrc status          # preview: lists what apply would write, writes nothing
uv tool install brainrc     # or: pipx install brainrc
brainrc apply               # write it
brainrc status              # check: prints "Everything in sync."
```

```text
$ uvx brainrc status
FETCH     gatework  https://github.com/brainrc/gatework.git (v0.8.0)
CREATE    claude    ~/.claude/CLAUDE.md
MERGE     claude    ~/.claude/settings.json  (hooks)
...

Dry run. Run `apply` to write.
$ brainrc apply
...
$ brainrc status
Everything in sync.
```

Next: [getting started](docs/getting-started.md) walks through what landed and how to add your own
rules and skills.

## Install

The `brainrc` command above covers all five tools, your own packs and the rules. Other ways in
(Homebrew, npx, a clone): [install](docs/install.md).

Only use Claude Code? It also installs as two plugins, without the rules or your own packs:

```text
/plugin marketplace add brainrc/brainrc
/plugin install brainrc@brainrc
```

That one carries the guard hooks. Gatework is the second, `gatework@gatework` ([plugins](docs/plugins.md)).

## Gatework

brainrc's default pack, [Gatework](https://github.com/brainrc/gatework), takes a ticket to a
reviewed pull request: spec, plan, implement, verify, document, deliver. Small agents do the work
and you approve three times: the spec, the plan, and the push.

```text
/brainrc-work gh:42          # a GitHub issue; also local:tickets/7.md or a sentence
```

It works best in Claude Code, where each role gets a fresh context and the guard hooks are
enforced. Elsewhere it is best effort ([details](docs/gatework.md#harness-support)). Don't want
it? Turn it off and brainrc installs only its rules and guard hooks ([packs](docs/packs.md#default-packs)).

## Why not …

| | Its own docs say | brainrc |
|---|---|---|
| [chezmoi](https://www.chezmoi.io/) | manages your dotfiles across multiple machines, securely | not a dotfile manager; it targets AI-tool config and their formats |
| [GNU Stow](https://www.gnu.org/software/stow/) | a dotfile organizer that symlinks separate directories into your home directory | links skills the same way, but also renders rules and merges hooks and MCP servers per tool |
| [Harness plugins](https://code.claude.com/docs/en/plugins) | a Claude Code plugin is a directory of skills, agents, hooks, and MCP servers installed as one unit | ships as one too; `brainrc` covers the other four tools |
| [rulesync](https://github.com/dyoshikawa/rulesync) | a Node.js CLI that generates config files for many AI tools from unified rule files | adds guard hooks, a lockfile and Gatework; a Python tool |
| brainrc's limits | | best on Claude Code; Codex, Antigravity and Cursor are best effort; needs uv (or Python 3.11+) outside Claude Code |

Also see [ruler](https://github.com/intellectronica/ruler) and [dotagents](https://github.com/getsentry/dotagents).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), the [code of conduct](CODE_OF_CONDUCT.md), and [AGENTS.md](AGENTS.md). Before committing, run `python3 scripts/brainrc.py validate` and `python3 -m unittest discover -s tests`.

## Security

Treat this repo as public. Don't commit secrets, tokens, internal hostnames, or absolute home-directory paths. Gitleaks runs in pre-commit and CI. To report a vulnerability, see [SECURITY.md](SECURITY.md).

## Privacy

brainrc sends no usage data and has no telemetry. Its own code makes no network calls. The only external commands it runs are `git`, to fetch packs you name by URL, and `ccusage`, only if you pass `--ccusage` to the retro script. The eval scripts run only the model command you configure.
