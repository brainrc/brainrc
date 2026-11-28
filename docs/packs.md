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
  overrides/claude/settings.fragment.json merged after the core fragment; {{hooks_dir}} = the pack's hooks dir (see Permissions)
  overrides/opencode/plugin.js            linked beside core's guard plugin, as brainrc-guard-acme.js
  mcp/servers.toml       MCP servers, synced after core's (see formats.md#mcp-servers-mcpserverstoml)
  tripwires.toml         patterns that must not appear in the pack (checked by validate)
```

Skills, agents, commands, and MCP servers must start with the pack's `prefix`, and no name may
exist in two sources unless `exclude` leaves one copy out; `apply` refuses to write anything
while one does. The full rules are in [Naming](#naming), and each file's format in
[formats](formats.md).

## Packs from one repo

A repo can hold several packs, one per folder, each with its own `pack.toml`. `subdir` next to
`git` and `ref` names the folder that is the pack:

```toml
[python]
git = "https://github.com/brainrc/packs.git"
ref = "v0.1.0"
subdir = "python"   # a folder inside the repo, using /; no `.` or `..`
```

`apply` fetches the repo into `$BRAINRC_HOME/packs/<key>` and installs from that folder; the rest
of the repo is never read. It fails, naming the folder, if the ref has no such folder or it's a
link rather than a folder; the clone stays at the commit it had. The lock records `subdir` next to `git`, `ref` and `commit`, so
`install --frozen` and `check` install and compare that folder at the locked commit
([lock format](project.md#brainrclock)). Each pack keeps a clone of its own, so two packs from one
repo can sit at different refs. `subdir` works the same in a repo's `brainrc.toml`.

## pack.toml

```toml
name = "acme"
prefix = "acme-"          # default: "<name>-"
id = "acme/acme-ai-pack"  # optional: the <owner>/<pack> ID it's published under (see Naming)
requires_api = "^1"       # pack API versions this pack works with (see Compatibility)
max_always_tokens = 800   # optional budget for rules + descriptions (see Context cost)
test = "tests"            # optional: tests validate --pack runs (see Pack tests)

[scope]                   # optional: where the pack applies (see Scope)
remotes = ["github.com/acme/*"]

[[guard.deny]]            # optional: commands core's guard refuses here (see Guard rules)
match = "acme-deploy prod"
reason = "deploys to production"

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
| `requires_api` | string | Pack API versions the pack works with, e.g. "^1"; core content releases never break it ([compatibility](#compatibility)). |
| `requires_core` | string | Deprecated: pin requires_api instead. Core versions the pack works with, e.g. ">=0.8, &lt;0.9"; ignored when requires_api is set ([compatibility](#compatibility)). |
| `max_always_tokens` | number | Budget for the tokens the pack loads into every session: rules plus descriptions ([context cost](#context-cost)). |
| `validator` | string | A Python module in the pack that checks what only it understands ([validator plugins](#validator-plugins)). |
| `test` | string | The pack's own unittest tests, a directory or a .py file in the pack; validate --pack runs them ([pack tests](#pack-tests)). |
| `scope` | table | Where the pack applies: any glob matching means it does; none means everywhere ([scope](#scope)). |
| `guard` | table | [[guard.deny]] and [[guard.ask]] rules core's guard hook enforces, with match or tool, reason and scope; deny rules may name a path or host for the OS sandbox instead ([guard rules](#guard-rules)). |
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
| `pack.toml` | name, prefix, `requires_api` for this pack API's major, a [token budget](#context-cost) and `test` |
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
in it but `.git` (`--force` replaces an earlier pack and keeps its `.git`), and `--enable` adds the pack to `packs.local.toml`.

[examples/pack-template](../examples/pack-template/README.md) holds the same files for a pack
called `mypack`, with steps for renaming it: the contents of a GitHub template repository, for
anyone who would rather start from **Use this template** than install brainrc first.
`scripts/pack_template.py` keeps it in step with `new pack`, and CI validates it.

## What `new <item>` writes

Inside a pack, `brainrc new <kind> <name>` writes one item that validates, with
the prefix applied and its frontmatter filled in, then checks the pack as `validate --pack` does
([options](commands.md#brainrc-new-skill)). It finds the pack from the folder you are in, or takes
`--pack DIR`, and never replaces an item without `--force`.

| Command | Writes |
|---|---|
| `new skill <name>` | `skills/<prefix><name>/SKILL.md` with `name` and `description` |
| `new skill <name> --domain GLOB,...` | a domain skill: Validate (offline), Conventions, Review checklist and Never without approval, and a [Domains row](#extensions) for those files in `pack.toml` |
| `new agent <name>` | `agents/<prefix><name>.md` with read-only `tools` (`Read, Grep, Glob`), `model = inherit`, and the handoff block it ends with |
| `new rule <name>` | `rules/NN-<name>.md` after the last rule, with `trigger: always_on` and `alwaysApply: true`; it prints the pack's always-loaded tokens against `max_always_tokens` |
| `new command <name>` | `commands/<prefix><name>.md` with `description` and `$ARGUMENTS`; `--as-skill` writes the user-invoked skill form Codex runs ([formats](formats.md#commands-commandsnamemd)) |

The bodies come from `brainrc/_templates/items`: headings with one line each that says what goes
there. Replace them before you publish the pack.

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
publishes it. Official packs are owned by `brainrc`. Gatework has a repo of its own; the others
are folders of [brainrc/packs](https://github.com/brainrc/packs), enabled with `subdir`
([packs from one repo](#packs-from-one-repo)):

| ID | What it holds | Issue |
|---|---|---|
| `brainrc/gatework` | the default pack: Gatework's engine, its roles, ticket connectors and general domain skills ([brainrc/gatework](https://github.com/brainrc/gatework)) | [#172](https://github.com/brainrc/brainrc/issues/172) |
| `brainrc/starter` | the small, measured base for the default profile ([starter](https://github.com/brainrc/packs/tree/main/starter)) | [#313](https://github.com/brainrc/brainrc/issues/313) |
| `brainrc/review` | review, PR description, commit message and unslop ([review](https://github.com/brainrc/packs/tree/main/review)) | [#314](https://github.com/brainrc/brainrc/issues/314) |
| `brainrc/go` | Go, built from today's `brainrc-go-service` skill ([go](https://github.com/brainrc/packs/tree/main/go)) | [#315](https://github.com/brainrc/brainrc/issues/315) |
| `brainrc/terraform-aws` | Terraform and AWS ([terraform-aws](https://github.com/brainrc/packs/tree/main/terraform-aws)) | [#316](https://github.com/brainrc/brainrc/issues/316) |
| `brainrc/kubernetes` | Kubernetes, including GitOps and containers ([kubernetes](https://github.com/brainrc/packs/tree/main/kubernetes)) | [#317](https://github.com/brainrc/brainrc/issues/317) |
| `brainrc/python` | Python: Ruff and pytest ([python](https://github.com/brainrc/packs/tree/main/python)) | [#183](https://github.com/brainrc/brainrc/issues/183) |
| `brainrc/node-ts` | Node and TypeScript: tsc and ESLint ([node-ts](https://github.com/brainrc/packs/tree/main/node-ts)) | [#184](https://github.com/brainrc/brainrc/issues/184) |
| `brainrc/rust` | Rust: rustfmt, Clippy and cargo test ([rust](https://github.com/brainrc/packs/tree/main/rust)) | [#185](https://github.com/brainrc/brainrc/issues/185) |
| `brainrc/security-baseline` | the default guard policy, secret protection and a sandbox profile ([security-baseline](https://github.com/brainrc/packs/tree/main/security-baseline)) | [#323](https://github.com/brainrc/brainrc/issues/323) |

`brainrc/go`, `brainrc/terraform-aws` and `brainrc/kubernetes` hold the domain skills Gatework
shipped up to 0.8, under the same names (#318). Gatework 0.9 no longer ships them, so enable the
packs for the stacks you use to keep those skills. If you pin Gatework 0.8, enable one beside it
by excluding Gatework's copy in `brainrc.local.toml`, for example
`exclude = ["gatework:skills/brainrc-kubernetes"]`: an excluded item isn't installed, so it
doesn't collide. `brainrc/starter` and
`brainrc/review` reuse Gatework's names too (`brainrc-project-commands`, and the review, PR
description, commit message and unslop skills): they are for a setup with Gatework off.

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

## Scope

`[scope]` says where a pack applies, so a work pack's deliver checks, guard rules and reviewers
stay out of your personal repos, in place of free text such as "in acme repos":

```toml
[scope]
remotes = ["github.com/acme/*", "git.acme.example.net/*"]   # a git remote of the repo you're in
paths = ["~/src/acme"]          # the directory you're in, or one above it; ~ and $VARS expand
kube_contexts = ["acme-*"]      # kubectl's current context ($KUBECONFIG or ~/.kube/config)
aws_profiles = ["acme-*"]       # $AWS_PROFILE, "default" when it isn't set
tickets = ["ACME-*"]            # a ticket ref in the branch name (acme-42-fix), or one passed in
```

Every value is a list of globs, and the pack applies when any one of them matches. A remote is
matched as written and as `host/owner/repo`, so one glob covers its SSH and HTTPS URLs. A pack
without `[scope]`, or with an empty one, applies everywhere, as before. The rules, skills and
agents a pack installs are still installed everywhere: scope decides where its extensions and
guard rules take effect.

`brainrc scope` lists each enabled pack as `APPLIES` or `SKIPPED` in the directory you're in and
says why, and `brainrc scope --extensions` prints the [extensions](#extensions) a run there
should read: only the packs that apply. The `extensions.md` that `apply` renders holds every
pack and ends with a Scope section saying where each scoped pack applies.

## Guard rules

A pack adds rules to core's guard in `pack.toml`, without a hook of its own:

```toml
[[guard.deny]]                 # refused
match = "acme-deploy prod"
reason = "deploys to production, which only the release pipeline does"

[[guard.ask]]                  # asked about first
tool = "mcp__acme-jira__*transition*"
reason = "moves an Acme ticket to another status"
scope = { kube_contexts = ["acme-*"] }   # optional: in place of the pack's [scope]
```

Each rule sets `reason` and one of `match` or `tool`. `match` is a command: its program (by name,
from any directory, after `VAR=value`, `sudo` or `env`) and then the other words in that order,
with other words and flags allowed between them; each word may be a glob. `tool` is a glob for an
MCP tool's full name. A rule takes effect only where the pack's [`[scope]`](#scope) matches the
directory the command runs in, or the rule's own `scope` when it sets one.

`apply` renders every enabled pack's rules, with their scopes, into
`$BRAINRC_HOME/guard-rules.json`, and core's `guard_outward.py` checks them on every Bash and MCP
call. Commands inside `sh -c`, `eval`, `$(…)` and backticks are unwrapped as for core's own rules.
A pack's deny wins over any ask; a pack's ask is shown when core has nothing to ask. Without the
file (no rules, or before the first `apply`), the guard behaves as before. `validate` checks each
rule. Claude Code, Cursor, OpenCode, Codex and Antigravity all enforce them through core's guard,
judging the scope where each runs the command; where a tool can't ask, a pack's ask blocks the call
and tells the model to ask you to run it ([guardrails](guardrails.md#gaps-by-tool)).

A `[[guard.deny]]` rule can set `path` or `host` instead, to reach what the hooks can't see (a
script that reads a file, a client that calls a host). `apply` compiles these into Claude Code's
sandbox settings in `~/.claude/settings.json`, which the OS enforces on every Bash command and its
child processes:

```toml
[[guard.deny]]
path = "~/.acme/credentials"   # sandbox.filesystem.denyRead and denyWrite
reason = "Acme's deploy keys"
scope = {}                     # the sandbox applies everywhere, so say so in a scoped pack

[[guard.deny]]
host = "*.acme.example"        # sandbox.network.deniedDomains
reason = "Acme's internal services"
scope = {}
```

`path` starts with `~/` or `/`; `host` is a domain, optionally `*.` first. These rules can't ask
and can't follow a `[scope]`, so `validate` refuses one under `[[guard.ask]]` or one that a scoped
pack leaves scoped. The entries brainrc adds are recorded in `settings-owned.json`, as permission
entries are: your own stay, and the pack's go when it's disabled or brainrc is uninstalled. They
take effect only where Claude Code's sandbox is on (`sandbox.enabled`), and the sandbox covers
Bash, not the Read tool or web fetches ([guardrails](guardrails.md#known-gaps)). Other tools have
no sandbox brainrc can write, so there these rules do nothing.

Test a rule with [`brainrc.testing`](#pack-tests) against core's hook, with `BRAINRC_HOME` set to
a directory holding the rendered file, and a near miss beside the risky command.

## Permissions

A pack's `overrides/claude/settings.fragment.json` can list permission entries, so it ships a
read-only allow list or hard denies without a hook:

```json
{
  "permissions": {
    "allow": ["Bash(acme-status:*)", "mcp__acme-jira__get_issue"],
    "deny": ["Bash(acme-deploy prod:*)"]
  }
}
```

`apply` adds each `allow`, `deny` and `ask` entry to the settings file after yours, and records the
ones it added in `$BRAINRC_HOME/settings-owned.json`. Disable the pack and the next `apply` removes
exactly those: an entry you had before the pack, or one another enabled pack still lists, stays.
`uninstall` takes them out too. Other keys under `permissions` (`defaultMode`, say) are set only
when the file has none, and stay. `brainrc.lock` records every entry as one of the pack's tool
grants, so `apply` lists a new one as `PERMS` and asks first ([why packs](packs/why-packs.md)).
The `minimal` profile installs no settings fragment, so a pack's permissions and hooks need
`recommended` or `full`.

## Extensions

`[extensions.<namespace>]` is a table another pack reads; core passes it through untouched. The
pack that owns the namespace checks it with its [validator plugin](#validator-plugins), and
`validate` warns about a table no enabled pack reads. Gatework, the default pack, owns
`[extensions.gatework]` above. `apply` renders every enabled pack's table into
`$BRAINRC_HOME/extensions.md` (default `~/.config/brainrc/extensions.md`), which Gatework reads
at intake. With no other packs enabled, the file says so and Gatework runs as before; with
Gatework disabled, there is no file.

The file also lists, under **Pack roles**, every agent the other packs install, with the path of
its file. A pack's agent adds to Gatework's roles and never replaces one, and a harness that
installs no agents (Codex, Antigravity, Cursor) can still run it as a role in the one-session
fallback by reading that file. The acme example's `acme-reviewer` is one.

A machine can add its own `[extensions.gatework]` in `brainrc.local.toml`
([configuration](configuration.md#brainrclocaltoml)); `extensions.md` lists it after every pack's.

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

Packs pin the **pack API**, the version of what packs can rely on, not brainrc's own version:

```toml
requires_api = "^1"
```

The pack API version is `PACK_API` in `brainrc/packapi.py` (now `1.0`). Core releases that change
only content (skills, rules, docs, fixes) leave it alone, so a pin survives them. `requires_api`
takes comma-separated clauses of `>=`, `>`, `<=`, `<`, `==`, `!=` or `^` and a version (missing
parts are zero, a bare version means `>=`, and `^1` means `>=1.0, <2`).

- Not satisfied → `validate` fails and `apply`/`status` write nothing, naming the pack.
- Missing → allowed, with a warning.
- Policy: a change that only adds to the contract bumps the pack API's MINOR; one that removes or
  changes anything in it bumps MAJOR, so `^N` never breaks. Something deprecated keeps working,
  and `validate --pack` warns about it, for at least one core minor release before a MAJOR bump
  may remove it. [CHANGELOG.md](../CHANGELOG.md) tags such changes **[pack contract]**.

**What pack API 1 freezes.** The keys, types and limits in the
[pack.toml](schemas/pack.toml.schema.json) and [mcp/servers.toml](schemas/mcp-servers.toml.schema.json)
schemas; the [layout](#layout) and the frontmatter each file needs; item kinds and agent models; the
[naming](#naming) patterns; and the names a [validator plugin](#validator-plugins) may define,
with the arguments core passes each function. [docs/schemas/pack-api/1.0.json](schemas/pack-api/1.0.json) is the frozen list.
Core's tests build the live contract (the schemas, the kinds, models, naming patterns and
validator calls from the code, and a written list of the layout) and fail when it differs from
the frozen list for `PACK_API`; `python3 scripts/pack_api.py --write` freezes a new version.

**`requires_core` is deprecated.** It pins core's own version (`VERSION`), which content releases
bump. It still works: without `requires_api` it is checked against core's version as before, and
`validate --pack` warns. With `requires_api` set, it is ignored, so keep it only for cores older
than the one that added `requires_api` (0.8.39 and older), which ignore it. It goes no sooner
than pack API 2.

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
[connector config](#connector-config); `requires_api` (or the deprecated `requires_core`); tripwires; and the pack's own
[tests](#pack-tests). A skill named in prose counts only when its name has a hyphen and starts with
the pack's prefix or a first part two known skills share, so "the follow-up skill" stays prose. A
relative link in a rule warns, since rules are rendered into each harness's own file; link a URL.
`apply` refuses a pack only for what would break the install (frontmatter, names, collisions,
tags, links in skills, agents and commands); the rest only `validate` reports.
