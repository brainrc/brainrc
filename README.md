# ai-config

One Git repo for AI coding-assistant configuration (skills, agents, slash
commands, rules, hooks, and MCP servers), written once and synced into every harness:
Claude Code, Codex CLI, OpenCode, Gemini CLI, and Cursor.

It includes **spec-agent**, a spec-driven agent team that takes a ticket to a reviewed PR
across application code *and* infrastructure: Go, Terraform/Terragrunt, AWS, Kubernetes/Helm,
GitOps, CI pipelines, containers, migrations, and observability.

## Complete a ticket

```
/work gh:42                 # or: /work local:tickets/7.md · /work add a --dry-run flag to the sync CLI
```

You approve the **spec**, the **plan**, and **delivery** (push, PR, ticket update). Everything
between runs on its own, with evidence at every step. Details: [docs/spec-agent.md](docs/spec-agent.md).
Try it safely first with [examples/sandbox](examples/sandbox/README.md).

## Layout

```
rules/          Global instructions, as ordered markdown fragments (00-core.md, 10-git.md, ...).
                Concatenated into CLAUDE.md / AGENTS.md / GEMINI.md.
skills/<name>/  Agent Skills: spec-agent engine, ticket connectors, domain skills (terraform, aws, ...).
agents/         Agent roles (analyst, architect, implementer, reviewers, verifier, doc-writer).
commands/       Slash commands / prompts (markdown + frontmatter, $ARGUMENTS placeholder).
mcp/            Canonical MCP server registry. Env var names only, never secret values.
overrides/      Harness-specific config (Claude guard hooks + settings fragment).
harnesses.toml  Where each harness reads each content type.
scripts/        aicfg.py: sync + validate (Python 3.11+, stdlib only).
docs/           spec-agent, guardrails, efficiency, formats, roadmap.
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

Files are **symlinked** from each harness back into this repo, so `git pull`
updates every harness at once. Re-run `apply` only after you add or remove
skills, agents, commands, or rules. For Claude Code, `apply` also merges the guard hooks into
`~/.claude/settings.json` (your other hooks are kept; a backup is written first).

`aicfg` never overwrites a file it doesn't manage. Pre-existing files show up as
`CONFLICT` for you to move into the repo or delete.

## Per-machine customization (never committed)

| File | Purpose |
|---|---|
| `harnesses.local.toml` | Disable a harness or change paths (`[cursor]` / `enabled = false`) |
| `rules/*.local.md` | Private rules appended after the shared ones (e.g. employer conventions) |

## Adding content

See [docs/formats.md](docs/formats.md). Before committing:

```bash
python3 scripts/aicfg.py validate
python3 -m unittest discover -s tests
```

## Security

This repo is public. Don't commit secrets, tokens, internal hostnames, or
absolute home-directory paths. Gitleaks runs in pre-commit and CI.
