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
whose clone doesn't match its `git` and `ref`. `apply` records the commit each ref resolved to,
and a hash of every file it installed, in `~/.config/brainrc/brainrc.lock`; a tag or branch that
moved shows as `MOVED` ([lockfile](project.md)).

## Layout

Same as this repo. Every folder is optional.

```
acme-ai-pack/
  pack.toml              name, prefix, extensions for other packs (see Extensions)
  validator.py           optional checks and renders of its own (see Validator plugins)
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
| `brainrc/gatework` | the default pack: spec-agent, its roles, ticket connectors and domain skills ([brainrc/gatework](https://github.com/brainrc/gatework)) | [#172](https://github.com/brainrc/brainrc/issues/172) |
| `brainrc/starter` | the small, measured base for the default profile | [#313](https://github.com/brainrc/brainrc/issues/313) |
| `brainrc/review` | review, PR description, commit message and unslop | [#314](https://github.com/brainrc/brainrc/issues/314) |
| `brainrc/go` | Go, built from today's `brainrc-go-service` skill | [#315](https://github.com/brainrc/brainrc/issues/315) |
| `brainrc/terraform-aws` | Terraform and AWS | [#316](https://github.com/brainrc/brainrc/issues/316) |
| `brainrc/kubernetes` | Kubernetes, including GitOps | [#317](https://github.com/brainrc/brainrc/issues/317) |
| `brainrc/security-baseline` | the default guard policy, secret protection and a sandbox profile | [#323](https://github.com/brainrc/brainrc/issues/323) |

## pack.toml

```toml
name = "acme"
prefix = "acme-"          # default: "<name>-"
id = "acme/acme-ai-pack"  # optional: the <owner>/<pack> ID it's published under (see Naming)
requires_core = ">=0.7, <0.8"   # core versions this pack works with (see Compatibility)
max_always_tokens = 800   # optional budget for rules + descriptions (see Context cost)

[extensions.gatework]      # what the gatework pack (spec-agent) reads; see Extensions
deliver_checks = [        # listed in the Deliver gate as done / not applicable / not run
  "Deploy plan reviewed by the owning team",
]

[[extensions.gatework.domains]]   # extra rows for spec-agent's Domains table
files = "`deploy/*.yaml`, `charts/acme-*`"
skills = ["acme-deploy"]
reviewer = "brainrc-infra-reviewer"

[[extensions.gatework.intake_context]]   # skills spec-agent runs after fetching the ticket
skill = "acme-context"
when = "every ticket"

[extensions.gatework.ticket]   # a connector for this pack's ticket refs, with its config
connector = "brainrc-ticket-jira"
refs = ["ACME-*"]
host = "acme.example.net"
```

## Extensions

`[extensions.<namespace>]` is a table another pack reads; core passes it through untouched. The
pack that owns the namespace checks it with its [validator plugin](#validator-plugins), and
`validate` warns about a table no enabled pack reads. Gatework, the default pack, owns
`[extensions.gatework]` above. `apply` renders every enabled pack's table into
`$BRAINRC_HOME/extensions.md` (default `~/.config/brainrc/extensions.md`), which spec-agent reads
at intake. With no other packs enabled, the file says so and spec-agent runs as before; with
Gatework disabled, there is no file.

The forms from before 0.7.0, the same keys directly under `[extensions]` or under
`[extensions.spec-agent]`, still work and warn until 0.8.0: move them under
`[extensions.gatework]`. `apply` no longer writes the old copy at
`skills/spec-agent/references/extensions.md`, and removes it.

A pack has at most one `[extensions.ticket]`: one connector and the refs it handles. A team
with two ticket systems splits them into two packs. The connector, core or the pack's own,
must follow the [connector contract](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/connectors.md), which
`validate` checks.

## Validator plugins

A pack can check what only it understands: `validator = "validator.py"` in `pack.toml` names a
Python module in the pack. Each name in it is optional:

| Name | What core does with it |
|---|---|
| `NAMESPACE` | the `[extensions.<namespace>]` table it owns (default: the pack's name) |
| `LEGACY_KEYS`, `LEGACY_NAMESPACES`, `REMOVED_IN` | older extension forms it still reads; `validate` warns until `REMOVED_IN` |
| `check_extensions(table, where, skill_names, agent_names)` | errors in one pack's table, before `apply` writes anything |
| `warn_extensions(table, where)` | warnings for one pack's table, from `validate` |
| `check(me, sources)` | errors across every source, from `validate` |
| `doctor(me)` | `(FAIL or WARN, what, fix)` findings for `doctor` |
| `render_extensions(tables)` | the text of `$BRAINRC_HOME/extensions.md` |

A validator is the pack's code running inside `brainrc`, so core runs it only for a default pack
(core's `packs.toml` pins it, or your own `packs.local.toml` points it elsewhere), for the pack
`validate --pack` checks, and for a pack whose entry in `packs.local.toml` sets
`run_validator = true`. Otherwise `validate` warns that the pack ships one. Gatework's
[validator.py](https://github.com/brainrc/gatework/blob/main/validator.py) is the reference.

## Default packs

A default pack is a table in core's shipped `packs.toml`: core turns it on unless
`packs.local.toml` says otherwise. Gatework is the only one: spec-agent (the `brainrc-gatework`
skill), its roles, the ticket connectors and the domain skills. It lives in
[brainrc/gatework](https://github.com/brainrc/gatework), and `packs.toml` pins it by `git` and a
release tag `ref`, so `apply` fetches it like any git pack (`update` refetches). Before 0.7.1 it
shipped inside core as `packs/gatework`.

Its names before 0.7.0 (`spec-agent`, `spec-status`, `ticket-github`, `kubernetes` and the rest,
listed in `brainrc/naming.py`) are deprecated aliases until 0.8.0, and the only names naming rule
7 lets it keep without its prefix. `[gatework]` with `enabled = false` in `packs.local.toml` turns
it off (`brainrc init` asks), and core then installs its rules and guard hooks and nothing else.
To try another version, set only `ref` there; to work on a clone, set `path`, which replaces the
shipped `git` and `ref`:

```toml
[gatework]
path = "~/src/gatework"
```

`validate --pack` checks a pack against core and the default packs on disk, so a pack that
extends Gatework is checked against it once `apply` has fetched it; until then `validate` warns
that it isn't fetched yet.

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
# A pack that extends Gatework or uses its skills and agents checks against it too:
git clone --depth 1 https://github.com/brainrc/gatework gatework
printf '[gatework]\npath = "%s/gatework"\n' "$PWD" > core/packs.local.toml
python3 core/scripts/brainrc.py validate --pack .
```

This checks the core, the default packs on disk and that pack, whatever else is in `packs.toml`:
frontmatter, cross-references (pack files may reference core's and Gatework's skills and agents),
the [naming](#naming) rules,
collisions, `pack.toml` extension references, `requires_core`, and tripwires.

## Packs and Claude Code plugins

Core also ships as a Claude Code plugin (README, Install). Packs stay `brainrc` packs: a plugin
could carry a pack's skills, agents, and hooks, but not its rules or its spec-agent extensions
(domains, ticket connector, Deliver checks), which `brainrc apply` renders for Gatework. Revisit if
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
