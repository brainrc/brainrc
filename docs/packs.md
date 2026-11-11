# Packs

A pack is a separate repo layered on top of this one. Use it for content that must not live
here: an employer's facts, internal skills, private review rules. This repo stays generic,
and each machine picks the packs it needs.

To start one, copy the working example in [examples/pack-acme](../examples/pack-acme/README.md).
For a pack with a guard hook, see [examples/pack-homelab](../examples/pack-homelab/README.md).

## Enable a pack

List it in `packs.local.toml` (gitignored; for an installed `brainrc`, in `~/.config/brainrc/`),
then apply:

```toml
[acme]
path = "~/src/acme-ai-pack"   # ~ and $VARS expand; relative paths are relative to this file
# enabled = false             # removes the pack's links and hooks on the next apply
```

```bash
python3 scripts/brainrc.py status   # dry run
python3 scripts/brainrc.py apply
```

Or name it by git URL and let `brainrc` fetch it, with no clone of your own:

```toml
[acme]
git = "git@github.com:acme/acme-ai-pack.git"   # any URL git accepts; private repos use your git credentials
ref = "v1.2.0"                                 # tag, branch, or commit; default: the remote's default branch
```

`apply` fetches it (shallow, detached) into `~/.config/brainrc/packs/acme` and records the URL
and `ref` it fetched; after that it works offline. Change `ref` or `git` and the next `apply`
fetches again (`status` shows the `FETCH` line first). A branch `ref` that hasn't changed isn't
refetched: `brainrc update` (or `python3 scripts/brainrc.py update`) refetches every git pack at its
`ref`, then applies. Both refuse a clone with local changes, and stop any git call after 60s.
Pin a tag, and bump `ref` to upgrade. `doctor` reports a git pack that hasn't been fetched yet or
whose clone doesn't match its `git` and `ref`.

## Layout

Same as this repo. Every folder is optional.

```
acme-ai-pack/
  pack.toml              name, prefix, spec-agent extensions
  skills/acme-*/         linked next to the core skills
  agents/acme-*.md       linked next to the core agents
  commands/acme-*.md
  rules/NN-*.md          rendered after all core rules, as one labelled block (see Rules)
  overrides/claude/hooks/                 linked to <hooks_dir>-acme (e.g. ~/.claude/hooks/brainrc-acme)
  overrides/claude/settings.fragment.json merged after the core fragment; {{hooks_dir}} = the pack's hooks dir
  mcp/servers.toml       MCP servers, synced after core's (see formats.md#mcp-servers-mcpserverstoml)
  tripwires.toml         patterns that must not appear in the pack (checked by validate)
```

Skills, agents, commands, and MCP servers must start with the pack's `prefix`, and no name may
exist in two sources. `apply` refuses to write anything if one does. The full rules are in
[Naming](#naming).

## Naming

A clear name is the cheapest trust signal a pack has. Every pack follows these seven rules:

1. **`brainrc-` and `brainrc/` are reserved for official packs.** No other pack's name, prefix
   or ID starts with them.
2. **A registry prefix starts with the owner's handle.** A pack published as `jdoe/k8s-tools`
   uses a prefix such as `jdoe-` or `jdoe-k8s-`.
3. **No vendor names without verification.** A pack's name, prefix and ID don't use a vendor's
   name (`aws`, `github`, `openai` and the like) unless the vendor itself is verified as its owner.
4. **No names one or two edits from an official name.** The official names are `brainrc` and
   the IDs in the table below, so `brainrx-` and `brianrc/review` are refused.
5. **ASCII lowercase letters, digits and hyphens only**, in names, prefixes, IDs and item names.
6. **A prefix is 2 to 24 characters**, not counting its trailing hyphen.
7. **Item names are prefix-scoped.** Every skill, agent, command and MCP server starts with the
   pack's prefix, so two packs' items can't collide.

`validate` and `apply` refuse a pack that breaks one. The vendor names and the official IDs it
checks are listed in `brainrc/naming.py`.

A pack's ID is `<owner>/<pack>`, where the owner is the GitHub user or organization that
publishes it. Official packs are owned by `brainrc`:

| ID | What it holds | Issue |
|---|---|---|
| `brainrc/starter` | the small, measured base for the default profile | [#313](https://github.com/brainrc/brainrc/issues/313) |
| `brainrc/review` | review, PR description, commit message and unslop | [#314](https://github.com/brainrc/brainrc/issues/314) |
| `brainrc/go` | Go, built from today's `go-service` skill | [#315](https://github.com/brainrc/brainrc/issues/315) |
| `brainrc/terraform-aws` | Terraform and AWS | [#316](https://github.com/brainrc/brainrc/issues/316) |
| `brainrc/kubernetes` | Kubernetes, including GitOps | [#317](https://github.com/brainrc/brainrc/issues/317) |
| `brainrc/security-baseline` | the default guard policy, secret protection and a sandbox profile | [#323](https://github.com/brainrc/brainrc/issues/323) |

## pack.toml

```toml
name = "acme"
prefix = "acme-"          # default: "<name>-"
id = "acme/acme-ai-pack"  # optional: the <owner>/<pack> ID it's published under (see Naming)
requires_core = ">=0.4, <0.6"   # core versions this pack works with (see Compatibility)
max_always_tokens = 800   # optional budget for rules + descriptions (see Context cost)

[[extensions.domains]]    # extra rows for spec-agent's Domains table
files = "`deploy/*.yaml`, `charts/acme-*`"
skills = ["acme-deploy"]
reviewer = "brainrc-infra-reviewer"

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

`apply` renders every enabled pack's extensions into `$BRAINRC_HOME/extensions.md` (default
`~/.config/brainrc/extensions.md`). spec-agent reads it at intake. The old copy at
`skills/spec-agent/references/extensions.md` is still written but deprecated: read the new path.
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
python3 core/scripts/brainrc.py validate --pack .
```

This checks the core plus that pack only, whatever is in `packs.toml`: frontmatter,
cross-references (pack files may reference core skills and agents), the [naming](#naming) rules,
collisions, `pack.toml` extension references, `requires_core`, and tripwires.

## Packs and Claude Code plugins

Core also ships as a Claude Code plugin (README, Install). Packs stay `brainrc` packs: a plugin
could carry a pack's skills, agents, and hooks, but not its rules or its spec-agent extensions
(domains, ticket connector, Deliver checks), which `brainrc apply` renders into core. Revisit if
plugins gain a way to extend another plugin.

## Context cost

`python3 scripts/brainrc.py tokens` estimates tokens per skill, agent, and command across all
enabled sources. It also shows what loads in every session (rules and descriptions) versus on
use. Keep pack rules short: they load in every session on that machine.

`validate` enforces a budget on each source's always-loaded tokens (its rules plus its skill,
agent, and command descriptions). Core's is 3,000. A pack declares its own in `pack.toml`:

```toml
max_always_tokens = 800
```

Over a declared budget, `validate` fails and names the biggest items. A pack without
`max_always_tokens` gets a warning above 1,000 tokens. Any description over 100 tokens gets a
warning: say what the skill does and when to use it, and move the rest into the body.
