# ai-config

One Git repo for AI coding-assistant configuration (skills, agents, slash
commands, rules, and hooks), written once and synced into Claude Code, Codex CLI, OpenCode,
Antigravity CLI, and Cursor. Skills reach every harness. Rules, commands, and agents reach only
some so far. Guard hooks are Claude Code only, and MCP servers aren't synced yet.
Details per harness: [harness support](docs/formats.md#harness-support).

It includes **spec-agent**, a spec-driven agent team that takes a ticket to a reviewed PR
across application code *and* infrastructure: Go, Terraform/Terragrunt, AWS, Kubernetes/Helm,
GitOps, CI pipelines, containers, migrations, and observability.

New here? Start with the [architecture overview](docs/architecture.md): one diagram and a glossary.

## Complete a ticket

```
/work gh:42                 # or: /work local:tickets/7.md · /work add a --dry-run flag to the sync CLI
```

You approve the **spec**, the **plan**, and **delivery** (push, PR, ticket update). Everything
between runs on its own, with evidence at every step. Details: [docs/spec-agent.md](docs/spec-agent.md).
Try it safely first with [examples/sandbox](examples/sandbox/README.md), and grade the run with
[evals](docs/evals.md).

## Layout

```
rules/          Global instructions, as ordered markdown fragments (00-core.md, 10-git.md, ...).
                Concatenated into CLAUDE.md / AGENTS.md.
skills/<name>/  Agent Skills: spec-agent engine, ticket connectors, domain skills (terraform, aws, ...).
agents/         Agent roles (analyst, architect, implementer, reviewers, verifier, doc-writer).
commands/       Optional, for packs: slash commands. Core's (/work, /review, /spec-*) are skills.
mcp/            Canonical MCP server registry. Env var names only, never secret values.
overrides/      Harness-specific config (Claude guard hooks + settings fragment).
harnesses.toml  Where each harness reads each content type.
packs.toml      Extra source repos ("packs") layered on top; usually set in packs.local.toml.
VERSION         Core version that packs pin with `requires_core`; changes in CHANGELOG.md.
aicfg/          The aicfg package: sync, validate, doctor, plugin, tokens (Python 3.11+, stdlib only).
scripts/        aicfg.py (runs the package), evals.py.
docs/           spec-agent, guardrails, efficiency, formats, troubleshooting, harness packages, roadmap.
tests/          stdlib unittest for aicfg and hooks.
examples/       Sandbox project + tickets for trying spec-agent.
dist/           Generated output (gitignored).
```

## Install

```bash
git clone <this-repo> ~/ai-config
cd ~/ai-config
python3 scripts/aicfg.py status   # dry run: shows what would be linked
python3 scripts/aicfg.py apply    # render rules + create symlinks
```

Skills, agents, commands, and hooks are **symlinked** from each harness back into this repo,
so `git pull` updates them in every harness at once. Rules are different: they are rendered
into `~/.config/ai-config/instructions.md` (`$AICFG_HOME` to change it), so re-run `apply` after any change to `rules/` (edits included),
and after you add or remove skills, agents, or commands. For Claude Code, `apply` also merges
the guard hooks into `~/.claude/settings.json` (your other hooks are kept; a backup is written
first, and the last 5 backups are kept).

### Install without a clone

`aicfg` also installs as a command, with core's skills, agents, rules, and hooks bundled:

```bash
uv tool install git+https://github.com/bxker/ai-config   # or: pipx install git+https://github.com/bxker/ai-config
aicfg status
aicfg apply
```

Links then point into the installed package, so `uv tool upgrade ai-config` (or `pipx upgrade
ai-config`) updates every harness. Local files go in `~/.config/ai-config/` (`$AICFG_HOME`):
`harnesses.local.toml`, `packs.local.toml`, and `rules/*.local.md`. Packs are local
directories or git URLs that `aicfg` fetches ([packs](docs/packs.md#enable-a-pack)). The fix
hints `doctor` prints show the checkout command; use `aicfg <command>`.
`plugin` needs a checkout. Contributors use the clone above.

`aicfg` never overwrites a file it doesn't manage. Pre-existing files show up as
`CONFLICT` for you to move into the repo or delete.

Something missing in a harness? `python3 scripts/aicfg.py doctor` checks the install without
changing anything: stale rules, missing or broken links (after moving the repo, say), broken
packs, unmerged hooks, and harnesses that aren't installed. Each problem comes with its fix.
[docs/troubleshooting.md](docs/troubleshooting.md) covers the rest, including how to uninstall.

### Claude Code plugin (no clone)

Claude Code users can install the skills (including `/work`), agents, and guard hooks as a plugin:

```text
/plugin marketplace add bxker/ai-config
/plugin install ai-config@ai-config
```

| Piece | Plugin | `aicfg` |
|---|---|---|
| Skills, agents | yes, named `ai-config:<name>` (`/ai-config:work`) | yes |
| Claude guard hooks | yes | yes |
| Rules (`rules/`) | no: plugins can't load instructions into every session | yes |
| Packs, other harnesses (Codex, OpenCode, Antigravity, Cursor) | no | yes |

Use one path, not both: together they load every skill and hook twice. For rules with the
plugin, copy `rules/*.md` into your own `~/.claude/CLAUDE.md`.

Codex installs the same plugin:

```text
codex plugin marketplace add bxker/ai-config
codex plugin add ai-config@ai-config
```

Codex gets the skills (`work`, `review`, `spec-*`, and the rest) and the agent files spec-agent
reads. Rules don't come with a Codex plugin: run `aicfg`, or copy `rules/*.md` into
`~/.codex/AGENTS.md`. Whether Codex runs the plugin's guard hooks is not yet verified
([harness packages](docs/harness-packages.md#codex)).

Antigravity CLI (`agy`) installs the repo as a plugin from the root
`plugin.json`:

```text
agy plugin install https://github.com/bxker/ai-config
```

It gets the skills, the agent files, and the rules: each `rules/*.md` carries
`trigger: always_on`, which Antigravity needs to load it. Guard hooks aren't included yet, so use
agy's own permission settings. This install was built from Antigravity's public docs and issues
and hasn't been run end to end
([harness packages](docs/harness-packages.md#antigravity-cli)).

### Platforms

macOS and Linux. Everything installs by symlink, and spec-agent reads its role files through
the `skills/spec-agent/roles` symlink, so the checkout needs symlinks too. On Windows, use WSL,
or turn on Developer Mode and run `git config --global core.symlinks true` before cloning.
`validate` and `doctor` report a checkout without symlinks, with the fix.

## Per-machine customization (never committed)

| File | Purpose |
|---|---|
| `harnesses.local.toml` | Disable a harness or change paths (`[cursor]` / `enabled = false`) |
| `packs.local.toml` | Layer extra repos on top: skills, agents, rules, hooks, spec-agent extensions ([docs/packs.md](docs/packs.md)) |
| `rules/*.local.md` | Private rules appended after the shared ones |

Content that must never live in this repo (an employer's facts and skills, for example) goes
in a **pack**: a separate repo with the same layout. See [docs/packs.md](docs/packs.md).
`python3 scripts/aicfg.py tokens` shows what each skill, agent, and rule costs in context.

## Adding content

New to it? Follow the [tutorial](docs/tutorial.md): build a pack with one domain skill in
about 15 minutes. Formats are in [docs/formats.md](docs/formats.md). To contribute to this
repo, see [CONTRIBUTING.md](CONTRIBUTING.md). Before committing:

```bash
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
```

## Security

This repo is public. Don't commit secrets, tokens, internal hostnames, or
absolute home-directory paths. Gitleaks runs in pre-commit and CI.
