<!-- divio: reference -->
# Packs reference

A pack is a folder or git repo of rules, skills, agents, commands, hooks and MCP servers, with a
`pack.toml` that names it. brainrc layers each pack you turn on over its own rules and guard hooks,
and installs the lot into every tool. This page is the reference: every file, key and rule.

- **Learn**: [your first pack](tutorial.md) builds one, step by step.
- **Do**: [use a pack](packs/use-a-pack.md), [import the files you have](packs/import.md),
  [validate a pack in its own CI](packs/validate-in-ci.md), or start a pack for
  [an employer](packs/employer-pack.md), [a team](packs/team-pack.md), [yourself](packs/personal-pack.md)
  or [a stack](packs/stack-pack.md), or [from a Claude Code plugin](packs/from-a-plugin.md).
- **Understand**: [why packs, and what you trust when you enable one](packs/why-packs.md).
- **Copy**: [examples/pack-acme](../examples/pack-acme/README.md) (every feature but hooks) and
  [examples/pack-homelab](../examples/pack-homelab/README.md) (a guard hook).

## Layout

Every folder is optional.

```
acme-ai-pack/
  pack.toml              name, prefix, extensions for other packs (see Extensions)
  validator.py           optional checks and renders of its own (see Validator plugins)
  tests/                 the pack's own tests, which validate --pack runs (see Pack tests)
  skills/acme-*/         linked into each tool's skills folder
  agents/acme-*.md       linked into each tool's agents folder
  commands/acme-*.md     linked into each tool's commands folder
  rules/NN-*.md          rendered after all core rules, as one labelled block (see Rules)
  overrides/claude/hooks/                 linked to <hooks_dir>-acme (e.g. ~/.claude/hooks/brainrc-acme)
  overrides/claude/settings.fragment.json merged after the core fragment; {{hooks_dir}} = the pack's hooks dir
  overrides/opencode/plugin.js            linked beside core's guard plugin, as brainrc-guard-acme.js
  mcp/servers.toml       MCP servers, synced after core's (see formats.md#mcp-servers-mcpserverstoml)
  tripwires.toml         patterns that must not appear in the pack (checked by validate)
```

Skills, agents, commands, and MCP servers must start with the pack's `prefix`, and no name may
exist in two sources. `apply` refuses to write anything if one does. The full rules are in
[Naming](#naming), and each file's format in [formats](formats.md).

## pack.toml

```toml
name = "acme"
prefix = "acme-"          # default: "<name>-"
id = "acme/acme-ai-pack"  # optional: the <owner>/<pack> ID it's published under (see Naming)
requires_core = ">=0.7, <0.9"   # core versions this pack works with (see Compatibility)
max_always_tokens = 800   # optional budget for rules + descriptions (see Context cost)
test = "tests"            # optional: tests validate --pack runs (see Pack tests)

[extensions.gatework]      # what Gatework reads; see Extensions
deliver_checks = [        # listed in the Deliver gate as done / not applicable / not run
  "Deploy plan reviewed by the owning team",
]

[[extensions.gatework.domains]]   # extra rows for Gatework's Domains table
files = "`deploy/*.yaml`, `charts/acme-*`"
skills = ["acme-deploy"]
reviewer = "brainrc-infra-reviewer"

[[extensions.gatework.intake_context]]   # skills Gatework runs after fetching the ticket
skill = "acme-context"
when = "every ticket"

[extensions.gatework.ticket]   # a connector for this pack's ticket refs, with its config
connector = "brainrc-ticket-jira"
refs = ["ACME-*"]
host = "acme.example.net"
blocked_status = "Blocked"
instructions = "Link the PR in the ticket's Development panel."   # see Connector config
```

`validate` checks `pack.toml` against
[`schemas/pack.toml.schema.json`](schemas/pack.toml.schema.json): a known key with a value of the
wrong type fails, and a key it doesn't know warns, naming the closest known key
(`max_always_token` → `max_always_tokens`), since brainrc would otherwise ignore it. Only
`validate` reports these; `apply` still installs the pack.

### Keys

Generated from [`pack.toml.schema.json`](schemas/pack.toml.schema.json) by
`scripts/pack_reference.py`:

<!-- generated: pack.toml.schema.json -->
| Key | Type | What it is |
|---|---|---|
| `name` | string | The pack's name; default: its packs.toml table or folder name. |
| `prefix` | string | What every skill, agent, command and MCP server name starts with; default: "&lt;name>-" ([naming](#naming)). |
| `id` | string | The &lt;owner>/&lt;pack> ID the pack is published under ([naming](#naming)). |
| `description` | string | One line on what the pack is for. |
| `requires_core` | string | Core versions the pack works with, e.g. ">=0.8, &lt;0.9" ([compatibility](#compatibility)). |
| `max_always_tokens` | number | Budget for the tokens the pack loads into every session: rules plus descriptions ([context cost](#context-cost)). |
| `validator` | string | A Python module in the pack that checks what only it understands ([validator plugins](#validator-plugins)). |
| `test` | string | The pack's own unittest tests, a directory or a .py file in the pack; validate --pack runs them ([pack tests](#pack-tests)). |
| `extensions` | table | Tables other packs read, one per namespace, e.g. [extensions.gatework]; the pack that owns a namespace checks it ([extensions](#extensions)). |
<!-- end generated -->

### Editor completion

A pack's `pack.toml` and `mcp/servers.toml` have JSON Schemas in [`docs/schemas/`](schemas.md)
(`pack.toml`, `mcp-servers.toml`), as does core's `harnesses.toml`. Editors that use
[Taplo](https://taplo.tamasfe.dev/) (VS Code's Even Better TOML, Zed, Helix) complete keys and flag
wrong ones from a first line naming the schema, which `brainrc import` writes for you:

```toml
#:schema https://raw.githubusercontent.com/brainrc/brainrc/main/docs/schemas/pack.toml.schema.json
name = "acme"
```

In a checkout of this repo, [`.taplo.toml`](../.taplo.toml) maps each file to its schema. Files
outside it (a pack's own repo, `~/.config/brainrc/harnesses.local.toml`) take the `#:schema` line.

## mcp/servers.toml

Each `[servers.<name>]` table is one MCP server, named with the pack's prefix
([MCP servers](formats.md#mcp-servers-mcpserverstoml)). A server has `command` or `url`, not both;
an HTTP server takes no `args` or `env_from`. Generated from
[`mcp-servers.toml.schema.json`](schemas/mcp-servers.toml.schema.json):

<!-- generated: mcp-servers.toml.schema.json -->
| Key | Type | What it is |
|---|---|---|
| `command` | string | A stdio server: the program to run. |
| `args` | array of strings | Arguments for command. |
| `url` | string | An HTTP server: its URL. |
| `env_from` | array of strings | Environment variables the harness passes to command; names only, never values. |
| `harnesses` | array of strings | The harnesses that get this server; default: every one brainrc writes MCP servers for. |
<!-- end generated -->

## What `new pack` writes

`brainrc new pack <name>` writes a pack that validates on its first run, with everything its own
repository needs ([options](commands.md#brainrc-new-pack)):

```bash
brainrc new pack acme              # writes ./acme, then checks it as validate --pack does
brainrc validate --pack acme
```

| File | What it's for |
|---|---|
| `pack.toml` | name, prefix, `requires_core` for this core's minor series, a [token budget](#context-cost) and `test` |
| `rules/10-<name>.md` | one short rule: load the facts skill instead of guessing |
| `skills/<prefix>facts/SKILL.md` | the facts agents would otherwise guess: repositories, hosts, tools, teams |
| `tripwires.toml` | a [tripwire](#tripwirestoml) against home folder paths; add one for each stale fact |
| `tests/test_pack.py` | [pack tests](#pack-tests): rules stay short, no secret values |
| `README.md`, `AGENTS.md` | how to use the pack, and the rules for whoever edits it; `CLAUDE.md` and `GEMINI.md` point at `AGENTS.md` for the tools that need it |
| `.github/workflows/validate.yml`, `.pre-commit-config.yaml` | the [validate-pack](packs/validate-in-ci.md) action and hook, pinned to this core's tag |
| `.gitignore` | keeps `*.local.*` files and caches out |

In a terminal it asks for the name, prefix, the tools you'll edit the pack with, and a ticket
system (`github`, `jira` or `local`), which becomes an `[extensions.gatework.ticket]` table. It
checks the [naming rules](#naming) before it writes anything, never writes into a folder with files
in it (`--force` replaces an earlier pack), and `--enable` adds the pack to `packs.local.toml`.

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
| `brainrc/gatework` | the default pack: Gatework's engine, its roles, ticket connectors and domain skills ([brainrc/gatework](https://github.com/brainrc/gatework)) | [#172](https://github.com/brainrc/brainrc/issues/172) |
| `brainrc/starter` | the small, measured base for the default profile | [#313](https://github.com/brainrc/brainrc/issues/313) |
| `brainrc/review` | review, PR description, commit message and unslop | [#314](https://github.com/brainrc/brainrc/issues/314) |
| `brainrc/go` | Go, built from today's `brainrc-go-service` skill | [#315](https://github.com/brainrc/brainrc/issues/315) |
| `brainrc/terraform-aws` | Terraform and AWS | [#316](https://github.com/brainrc/brainrc/issues/316) |
| `brainrc/kubernetes` | Kubernetes, including GitOps | [#317](https://github.com/brainrc/brainrc/issues/317) |
| `brainrc/security-baseline` | the default guard policy, secret protection and a sandbox profile | [#323](https://github.com/brainrc/brainrc/issues/323) |

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

## Extensions

`[extensions.<namespace>]` is a table another pack reads; core passes it through untouched. The
pack that owns the namespace checks it with its [validator plugin](#validator-plugins), and
`validate` warns about a table no enabled pack reads. Gatework, the default pack, owns
`[extensions.gatework]` above. `apply` renders every enabled pack's table into
`$BRAINRC_HOME/extensions.md` (default `~/.config/brainrc/extensions.md`), which Gatework reads
at intake. With no other packs enabled, the file says so and Gatework runs as before; with
Gatework disabled, there is no file.

The old forms from before 0.7.0, the same keys directly under `[extensions]` or under
`[extensions.spec-agent]`, still work with a warning: move them under `[extensions.gatework]`.

A pack has at most one `[extensions.gatework.ticket]`: one connector and the refs it handles. A team
with two ticket systems splits them into two packs. The connector, core or the pack's own,
must follow the [connector contract](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/connectors.md), which
`validate` checks.

### Connector config

A connector skill declares the keys its table takes, and their types, in its SKILL.md frontmatter
under the [Agent Skills](https://agentskills.io) `metadata` map, so every harness still loads it:

```markdown
---
name: acme-ticket-desk
description: Ticket connector for the Acme service desk. Use for DESK- refs.
metadata:
  brainrc-config: "refs: list required; queue: integer; blocked_status: string"
---
```

Each `key: type` entry is one of `string`, `integer`, `boolean` or `list` (of strings), followed by
`required` when the table must set it. `validate` then checks every pack table that names the skill
as its `connector`: a key of the wrong type or a missing required key fails, and a key the
connector doesn't declare warns. Only `validate` reports these; `apply` still installs the pack. A
connector that declares nothing, or a declaration with a mistake (which fails on the skill), isn't
checked. Every table may also set `instructions`: what the pack tells the connector about its
tickets, in place of free-form keys such as `notes`. It reaches the model, so the pack's
[tripwires](#tripwirestoml) check it like the pack's other text, unless a tripwire sets `paths` or
`exclude`s `pack.toml`.

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

## Pack tests

`test = "tests"` in `pack.toml` names the pack's own `unittest` tests: a directory (its `test*.py`
files) or one `.py` file. `validate --pack` runs them in a fresh Python, from the pack's root, and
fails if one fails or none is found. They are the pack's code, so only `validate --pack` from the
command line runs them; `doctor` and `apply` never do.

`brainrc.testing` runs a guard hook the way Claude Code does, a PreToolUse payload on stdin, so a
test needs no scaffolding of its own. A string is a Bash command; a dict is the whole payload:

```python
from brainrc.testing import assert_allows, assert_asks, assert_denies, assert_no_opinion, run_hook

HOOK = Path(__file__).resolve().parent.parent / "overrides/claude/hooks/guard_acme.py"

class GuardTest(unittest.TestCase):
    def test_asks_before_a_deploy(self):
        assert_asks(HOOK, "acme deploy prod")      # the risky command
        assert_allows(HOOK, "acme deploy --help")  # and a safe near-miss
```

`assert_allows` passes when the hook allows or has no opinion, and `assert_no_opinion` only when it
stays out, so Claude Code's own permission check still decides; `assert_denies` counts exit code 2
as a deny. Each lists every case that came out wrong, and a missing, failing or hung hook fails.
`run_hook(hook, payload)` returns the decision itself. [pack-homelab](../examples/pack-homelab/tests/test_guard.py)
has a full example.

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

## Compatibility

brainrc's version is in `VERSION`. [CHANGELOG.md](../CHANGELOG.md) tags changes that affect packs
with **[pack contract]**. Declare the versions your pack supports with `requires_core`:
comma-separated clauses of `>=`, `>`, `<=`, `<`, `==`, `!=` and a version (missing parts
are zero, and a bare version means `>=`).

- Not satisfied → `validate` fails and `apply`/`status` write nothing, naming the pack.
- Missing → allowed, with a warning.
- Policy: semver. While core is `0.x`, a breaking pack-contract change bumps MINOR, so pin
  `">=0.N, <0.N+1"`. After `1.0`, breaking changes bump MAJOR: pin `">=1.N, <2"`.
  Other changes (new skills, fixes, docs) bump PATCH and never break a pin.

## Context cost

`brainrc tokens` estimates tokens per skill, agent, and command across all
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

## What validate checks

This checks the core, the default packs on disk and that pack, whatever else is in `packs.toml`:
frontmatter; `pack.toml` against [its schema](#packtoml); cross-references in skills, agents,
commands, rules, `README.md` and `docs/**` (relative links, `[agent: x]` tags, and skills named
as "`x` skill" or in prose as "the x skill"; pack files may reference core's and Gatework's skills
and agents); the [naming](#naming) rules; collisions; extension references and
[connector config](#connector-config); `requires_core`; tripwires; and the pack's own
[tests](#pack-tests). A skill named in prose counts only when its name has a hyphen and starts with
the pack's prefix or a first part two known skills share, so "the follow-up skill" stays prose. A
relative link in a rule warns, since rules are rendered into each harness's own file; link a URL.
`apply` refuses a pack only for what would break the install (frontmatter, names, collisions,
tags, links in skills, agents and commands); the rest only `validate` reports.
