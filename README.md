# brainrc

**spec-agent** takes a ticket to a reviewed pull request: spec → plan → implement → verify →
document → deliver, run by a team of small agents, with your approval at three gates. It covers
application code *and* infrastructure: Go, Terraform/Terragrunt, AWS, Kubernetes/Helm, GitOps,
CI pipelines, containers, migrations, and observability.

```
/work gh:42                 # or: /work local:tickets/7.md · /work add a --dry-run flag to the sync CLI
```

You approve the **spec**, the **plan**, and **delivery** (push, PR, ticket update). Everything
between runs on its own, with evidence at every step. Details: [docs/spec-agent.md](docs/spec-agent.md).

> **Harness support is not equal.** Each role gets a fresh context, and the guard hooks are
> enforced, only in **Claude Code**. **OpenCode** also runs roles as real subagents, but every
> role uses the same model and its hooks block instead of asking. In **Codex, Antigravity CLI,
> and Cursor**, spec-agent switches roles inside one session, so its reviewers are not
> independent of the implementer. Treat those three as best effort
> ([details](docs/spec-agent.md#harness-support)).

## Try it

1. Install (below), then copy the [sandbox](examples/sandbox/README.md) somewhere safe and run
   `/work local:tickets/001-add-shout-flag.md` in it.
2. Grade the run: `python3 scripts/evals.py check /tmp/spec-sandbox evals/cases/sandbox-001.toml`
   ([evals](docs/evals.md)). Recorded runs: [docs/e2e-runs.md](docs/e2e-runs.md).

New here? The [architecture overview](docs/architecture.md) has one diagram and a glossary.

## Install

Quickest, in Claude Code:

```text
/plugin marketplace add brainrc/brainrc
/plugin install brainrc@brainrc
```

For other tools, or to also get the shared rules and private packs, use **brainrc**, the syncer
in this repo. It writes skills, agents, commands, rules, hooks, and MCP servers once and links
them into Claude Code, Codex CLI, OpenCode, Antigravity CLI, and Cursor:

```bash
git clone https://github.com/brainrc/brainrc ~/brainrc && cd ~/brainrc
python3 scripts/brainrc.py apply
```

Every install path, each harness plugin, platform notes, release pinning, and per-machine
overrides: [docs/install.md](docs/install.md).

## More

| Doc | For |
|---|---|
| [spec-agent](docs/spec-agent.md) | stages, roles, domain skills, living specs, harness support |
| [guardrails](docs/guardrails.md) | what the hooks catch, their gaps, and the recommended setup for runs that touch real infrastructure |
| [post-deliver](docs/post-deliver.md) | design: following a PR through CI, review, and merge |
| [packs](docs/packs.md) · [tutorial](docs/tutorial.md) | private skills and rules in a separate repo |
| [formats](docs/formats.md) · [troubleshooting](docs/troubleshooting.md) · [roadmap](docs/roadmap.md) | reference |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), the
[code of conduct](CODE_OF_CONDUCT.md), and the rules in [AGENTS.md](AGENTS.md). Before committing:

```bash
python3 scripts/brainrc.py validate
python3 -m unittest discover -s tests
```

## Security

This repo is public. Don't commit secrets, tokens, internal hostnames, or
absolute home-directory paths. Gitleaks runs in pre-commit and CI. To report a
vulnerability, see [SECURITY.md](SECURITY.md).

## Privacy

brainrc sends no usage data and has no telemetry. Its own code makes no network calls. The only
external commands it runs are `git`, to fetch packs you name by URL, and `ccusage`, only if you
pass `--ccusage`.
