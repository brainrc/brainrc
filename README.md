# brainrc

Write your AI-tool config once and sync it into **Claude Code, Codex CLI, OpenCode, Antigravity
CLI, and Cursor**. Skills reach all five tools. Rules, commands, agents, hooks, and MCP servers
reach only some, because the tools differ ([harness support](docs/formats.md#harness-support)).

## Quickstart

Needs Python 3.11+ and git.

```bash
git clone https://github.com/brainrc/brainrc ~/brainrc
cd ~/brainrc
python3 scripts/brainrc.py status
python3 scripts/brainrc.py apply
python3 scripts/brainrc.py status
```

The first `status` previews what `apply` would write and writes nothing. It worked when the last
`status` prints `Everything in sync.`

```text
$ python3 scripts/brainrc.py status
CREATE    claude    ~/.claude/skills/brainrc-aws
...                 (about 160 lines, one per file)
MERGE     cursor    ~/.cursor/hooks.json  (hooks)

Dry run. Run `apply` to write.
$ python3 scripts/brainrc.py apply
CREATE    claude    ~/.claude/skills/brainrc-aws
...
MERGE     cursor    ~/.cursor/hooks.json  (hooks)
$ python3 scripts/brainrc.py status
Everything in sync.
```

## Install

In Claude Code, the quickest path:

```text
/plugin marketplace add brainrc/brainrc
/plugin install brainrc@brainrc
```

It carries the guard hooks; Gatework (spec-agent) is its own plugin, `gatework@gatework`. Plugins cover
Claude Code only. For the other tools, rules and private packs, use the syncer above. All install
paths, platform notes, and pinning: [docs/install.md](docs/install.md).

## Why not …

| | Its own docs say | brainrc |
|---|---|---|
| [chezmoi](https://www.chezmoi.io/) | manages your dotfiles across multiple machines, securely | not a dotfile manager; it targets AI-tool config and their formats |
| [GNU Stow](https://www.gnu.org/software/stow/) | a dotfile organizer that symlinks separate directories into your home directory | links skills and similar files the same way, but also renders rules and merges hooks and MCP servers per tool |
| [Harness plugins](https://code.claude.com/docs/en/plugins) | a Claude Code plugin is a directory of skills, agents, hooks, and MCP servers installed as one unit | ships as one too; the syncer covers the other four tools |
| [rulesync](https://github.com/dyoshikawa/rulesync) | a Node.js CLI that generates config files for many AI tools from unified rule files | ships guard hooks and installs Gatework (spec-agent) as its default pack; rulesync is a Node tool, brainrc needs Python |
| brainrc's limits | | best on Claude Code; Codex, Antigravity, Cursor are best effort; needs Python 3.11+ and a clone outside Claude Code |

Also see [ruler](https://github.com/intellectronica/ruler) and [dotagents](https://github.com/getsentry/dotagents).

## spec-agent

**spec-agent** takes a ticket to a reviewed pull request: spec → plan → implement → verify →
document → deliver, run by a team of small agents, with your approval at three gates. It covers
application code *and* infrastructure.

```
/brainrc-work gh:42                 # or: /brainrc-work local:tickets/7.md · /brainrc-work add a --dry-run flag to the sync CLI
```

You approve the **spec**, the **plan**, and **delivery** (push, PR, ticket update). Everything
between runs on its own, with evidence at every step. It lives in [Gatework](https://github.com/brainrc/gatework), the default pack. Details: [docs/spec-agent.md](docs/spec-agent.md).

> **Harness support is not equal.** Each role gets a fresh context, and the guard hooks are
> enforced, only in **Claude Code**. **OpenCode** also runs roles as real subagents, but every
> role uses the same model and its hooks block instead of asking. In **Codex, Antigravity CLI,
> and Cursor**, spec-agent switches roles inside one session, so its reviewers are not independent
> of the implementer. Treat those three as best effort ([details](docs/spec-agent.md#harness-support)).

## More

| Doc | For |
|---|---|
| [guardrails](docs/guardrails.md) · [post-deliver](docs/post-deliver.md) | what the hooks catch and their gaps; following a PR through CI and merge |
| [packs](docs/packs.md) · [tutorial](docs/tutorial.md) · [project lock](docs/project.md) | private skills and rules in a separate repo; a repo's own packs, pinned in `brainrc.lock` |
| [formats](docs/formats.md) · [troubleshooting](docs/troubleshooting.md) · [roadmap](docs/roadmap.md) · [architecture](docs/architecture.md) | reference |
| [sandbox](examples/sandbox/README.md) · [evals](docs/evals.md) · [e2e runs](docs/e2e-runs.md) | try spec-agent on a toy repo and grade the run |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), the [code of conduct](CODE_OF_CONDUCT.md), and [AGENTS.md](AGENTS.md). Before committing, run `python3 scripts/brainrc.py validate` and `python3 -m unittest discover -s tests`.

## Security

Treat this repo as public. Don't commit secrets, tokens, internal hostnames, or absolute home-directory paths. Gitleaks runs in pre-commit and CI. To report a vulnerability, see [SECURITY.md](SECURITY.md).

## Privacy

brainrc sends no usage data and has no telemetry. Its own code makes no network calls. The only external commands it runs are `git`, to fetch packs you name by URL, and `ccusage`, only if you pass `--ccusage` to the retro script. The eval scripts run only the model command you configure.
