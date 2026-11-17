# Packs

A pack is a folder or git repo of rules, skills, agents, commands, hooks and MCP servers, with a
`pack.toml` that names it. brainrc layers each pack you turn on over its own rules and guard hooks,
and installs the lot into every tool.

Use a pack for anything brainrc itself shouldn't carry: your team's conventions, internal skills,
an employer's facts, private review rules. Each machine picks the packs it needs, and a repo can
pin its own ([team setup](project.md)).

- **Use packs**: [enable one](#enable-a-pack), [turn the default pack off or pin it](#default-packs),
  or [import the instruction files you have](#import).
- **Write one**: start from [your first pack](tutorial.md), or copy
  [examples/pack-acme](../examples/pack-acme/README.md) (every feature but hooks) or
  [examples/pack-homelab](../examples/pack-homelab/README.md) (a guard hook). The rest of this
  page is the reference.

## Enable a pack

List it in `packs.local.toml` ([where that file lives](configuration.md#where-the-files-live)),
then apply:

```toml
[acme]
path = "~/src/acme-ai-pack"   # ~ and $VARS expand; relative paths are relative to this file
# enabled = false             # removes the pack's links and hooks on the next apply
```

```bash
brainrc status   # preview
brainrc apply
```

Or name it by git URL and let brainrc fetch it, with no clone of your own:

```toml
[acme]
git = "git@github.com:acme/acme-ai-pack.git"   # any URL git accepts; private repos use your git credentials
ref = "v1.2.0"                                 # tag, branch, or commit; default: the remote's default branch
```

`apply` fetches it into `~/.config/brainrc/packs/acme`; after that it works offline. It records
the commit the ref resolved to, and a hash of every file it installed, in
`~/.config/brainrc/brainrc.lock`, and from then on **keeps the pack at that commit**, even when the
tag or branch moves. To move it:

- `brainrc update [<pack> ...]` refetches at the `ref`, prints the commits and files that change,
  then applies ([pinned commits](project.md#pinned-commits-and-update)).
- Changing `ref` or `git` fetches the new one on the next `apply` (`status` shows a `FETCH` line).

Both refuse a clone with local changes, and stop any git call after 60 seconds. Pin a tag, and
bump `ref` to upgrade. `doctor` reports a git pack that isn't fetched yet or doesn't match its
`git` and `ref`.

The lock also records what each pack can do: its hooks, MCP servers, tool grants and network
domains. `status` lists any added (`PERMS ... +`) or removed, and `apply` asks before adding any
unless you pass `--yes` ([permissions](project.md#permissions)).

## Default packs

A default pack is on unless you turn it off. [Gatework](gatework.md) is the only one: its engine
(the `brainrc-gatework` skill), its roles, the ticket connectors and the domain skills. It lives in
[brainrc/gatework](https://github.com/brainrc/gatework), and brainrc's own `packs.toml` pins it to a
release tag, so `apply` fetches it like any git pack.

In `packs.local.toml`:

```toml
[gatework]
enabled = false        # turn it off: brainrc then installs only its rules and guard hooks
```

```toml
[gatework]
ref = "v<X.Y.Z>"       # pin another Gatework release; its git URL is kept
```

```toml
[gatework]
path = "~/src/gatework"   # work on a clone; replaces the shipped git and ref
```

`brainrc init` asks whether to keep it. Gatework still installs its old names (`spec-agent`,
`spec-status`, `kubernetes` and the rest, listed in `brainrc/naming.py`) as deprecated aliases;
they are the only unprefixed names naming rule 7 lets it keep ([old names](upgrade.md#from-spec-agent)).

`validate --pack` checks a pack against brainrc and the default packs on disk, so a pack that
extends Gatework is checked against it once `apply` has fetched it; until then `validate` warns.
`--fetch-defaults` fetches them at the versions brainrc pins instead
([CI](#validate-a-pack-in-its-own-ci)).

## Import

`brainrc import PATH ...` writes the instruction files you already have as a pack, so they move
over in one command. A folder means the files in it that brainrc reads.

| Source | Becomes |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | one rule per section, in order |
| Cursor: `.cursor/rules/**/*.mdc`, `.cursorrules` | `alwaysApply: true` rules and `.cursorrules` become rules; a rule scoped by `globs` becomes a skill with a row in Gatework's Domains table for those globs; one with only a `description` becomes a skill with that description |
| Copilot: `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md` | copilot-instructions.md becomes one rule per section; a path-specific file with `applyTo: "**"` becomes a rule, one scoped to other globs a skill with a Domains row, one with neither a skill loaded on request, as for Cursor; one for code review only (`excludeAgent: coding-agent`) is skipped |

Each file is split at the shallowest heading level it uses more than once (a lone `# Title`
stays with the text under it), and each part becomes `rules/NN-<heading>.md` with a first-line
comment naming the file and lines it came from. Headings inside code blocks don't count. A
CLAUDE.md line that is only `@path` (Claude Code's import) is replaced by that file's rules, and
a brainrc project block is left out, since `install` writes it.

```bash
brainrc import ~/.claude/CLAUDE.md --name mine --enable   # write ~/.config/brainrc/imported/mine, load it
brainrc import . --to tools/agent-pack --dry-run          # what a repo's files would become
```

The pack goes to `$BRAINRC_HOME/imported/<name>` unless `--to` names a folder, and is checked as
`validate --pack` would. `import` never overwrites a folder with files in it; `--force` replaces
an earlier pack there (a folder with a `pack.toml`), never one that holds a source. `--enable` adds it to `packs.local.toml`; for one project, list it in `brainrc.toml` instead
([team setup](project.md)).

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
## Validate a pack in its own CI

The `validate-pack` action checks a pack against the core version you pin, and against core's
default packs (Gatework) at the versions that core pins, so a pack may use their skills and agents:

```yaml
- uses: actions/checkout@<sha>
- uses: brainrc/brainrc/.github/actions/validate-pack@<core tag or sha>
  with:
    path: .                  # the pack's directory (default: the repository root)
    # default-packs: "false" checks it against core alone
    # python-version: "3.12" sets one up; by default it uses the python3 on PATH
```

The ref you pin is the core: GitHub runs the action from that commit of this repository, so
there is nothing else to clone. To check before each commit, add the pre-commit hook, which
installs `brainrc` at the `rev` you pin:

```yaml
- repo: https://github.com/brainrc/brainrc
  rev: <core tag>
  hooks:
    - id: brainrc-validate-pack
      # args: [pack]          # the pack's directory, when it isn't the repository root
```

Both run `validate --pack <dir> --fetch-defaults`, which fetches the default packs at the refs
core's `packs.toml` pins into clones of their own under `$BRAINRC_HOME/validate-packs/` (once;
later runs reuse them), never the clones `apply` links.

Without either, clone core at the version you pin and run it yourself:

```bash
git clone --depth 1 --branch <core tag> https://github.com/brainrc/brainrc core
python3 core/scripts/brainrc.py validate --pack . --fetch-defaults
```

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

## Packs and Claude Code plugins

brainrc also ships as a Claude Code plugin ([plugins](plugins.md)), but packs need the `brainrc`
command: a plugin could carry a pack's skills, agents and hooks, but not its rules or its Gatework
extensions (domains, ticket connector, Deliver checks), which `brainrc apply` renders. This may
change if plugins gain a way to extend another plugin.
