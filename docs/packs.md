# Packs

A pack is a separate repo layered on top of this one. Use it for content that must not live
here: an employer's facts, internal skills, private review rules. This repo stays generic,
and each machine picks the packs it needs.

To start one, copy the working example in [examples/pack-acme](../examples/pack-acme/README.md).

## Enable a pack

List it in `packs.local.toml` (gitignored), then apply:

```toml
[acme]
path = "~/src/acme-ai-pack"   # ~ and $VARS expand; relative paths are relative to this repo
# enabled = false             # removes the pack's links and hooks on the next apply
```

```bash
python3 scripts/aicfg.py status   # dry run
python3 scripts/aicfg.py apply
```

## Layout

Same as this repo. Every folder is optional.

```
acme-ai-pack/
  pack.toml              name, prefix, spec-agent extensions
  skills/acme-*/         linked next to the core skills
  agents/acme-*.md       linked next to the core agents
  commands/acme-*.md
  rules/NN-*.md          rendered after all core rules, as one labelled block (see Rules)
  overrides/claude/hooks/                 linked to <hooks_dir>-acme (e.g. ~/.claude/hooks/ai-config-acme)
  overrides/claude/settings.fragment.json merged after the core fragment; {{hooks_dir}} = the pack's hooks dir
  tripwires.toml         patterns that must not appear in the pack (checked by validate)
```

Skills, agents, and commands must start with the pack's `prefix`, and no name may exist in
two sources. `apply` refuses to write anything if one does.

## pack.toml

```toml
name = "acme"
prefix = "acme-"          # default: "<name>-"
requires_core = ">=0.3, <0.4"   # core versions this pack works with (see Compatibility)

[[extensions.domains]]    # extra rows for spec-agent's Domains table
files = "`deploy/*.yaml`, `charts/acme-*`"
skills = ["acme-deploy"]
reviewer = "infra-reviewer"

[[extensions.intake_context]]   # skills spec-agent runs after fetching the ticket
skill = "acme-context"
when = "every ticket"

[extensions.ticket]       # a connector for this pack's ticket refs, with its config
connector = "ticket-jira"
refs = ["ACME-*"]
host = "acme.example.net"

[extensions]
deliver_checks = [        # listed in the Deliver gate as done / not applicable / not run
  "Deploy plan reviewed by the owning team",
]
```

`apply` renders every enabled pack's extensions into
`skills/spec-agent/references/extensions.md` (gitignored). spec-agent reads it at intake.
With no packs enabled, the file says so and spec-agent runs as before.

A pack has at most one `[extensions.ticket]`: one connector and the refs it handles. A team
with two ticket systems splits them into two packs. The connector, core or the pack's own,
must follow the [connector contract](../skills/spec-agent/references/connectors.md), which
`validate` checks.

## Rules

The rendered instructions file has three parts, in this order:

1. Core rules, in filename order.
2. Each enabled pack's rules, one block per pack in `packs.toml` order, filename order inside.
   Each block starts with `<!-- pack: <name> -->` and a line telling the model the rules refine
   the ones above.
3. `*.local.md` rules from any source, under `<!-- local -->`.

Pack rule numbers only order rules within the pack. Later rules refine earlier ones and must
not contradict them: a pack rule that contradicts core is a bug in the pack. Write it as a
narrower case ("in Acme repos, also ...") instead.

## Compatibility

Core's version is in `VERSION`. [CHANGELOG.md](../CHANGELOG.md) tags changes that affect packs
with **[pack contract]**. Declare the versions your pack supports with `requires_core`:
comma-separated clauses of `>=`, `>`, `<=`, `<`, `==`, `!=` and a version (missing parts
are zero, and a bare version means `>=`).

- Not satisfied → `validate` fails and `apply`/`status` write nothing, naming the pack.
- Missing → allowed, with a warning.
- Policy: semver. While core is `0.x`, a breaking pack-contract change bumps MINOR, so pin
  `">=0.N, <0.N+1"`. After `1.0`, breaking changes bump MAJOR: pin `">=1.N, <2"`.
  Other changes (new skills, fixes, docs) bump PATCH and never break a pin.

## tripwires.toml

Stale facts that must not come back, checked by `validate`:

```toml
[[tripwire]]
id = "old-pager"
pattern = '(?i)\bpagerbot\b'
message = "pagerbot was replaced by the new on-call tool"
allow = '(?i)replaced|decommissioned|never'   # lines matching this pass (they warn against it)
paths = ["*.md"]                              # default; fnmatch against the path in the pack
```

## Validate a pack in its own CI

```bash
git clone <core-repo> core
python3 core/scripts/aicfg.py validate --pack .
```

This checks the core plus that pack only, whatever is in `packs.toml`: frontmatter,
cross-references (pack files may reference core skills and agents), name prefixes and
collisions, `pack.toml` extension references, `requires_core`, and tripwires.

## Context cost

`python3 scripts/aicfg.py tokens` estimates tokens per skill, agent, and command across all
enabled sources. It also shows what loads in every session (rules and descriptions) versus on
use. Keep pack rules short: they load in every session on that machine.
