# Commands

Every `brainrc` command and option. `brainrc --help` lists the commands and
`brainrc <command> --help` shows one command's options. From a clone, run
`python3 scripts/brainrc.py <command>` instead. `brainrc` with no command runs `status`, and
`brainrc --version` prints the version.

A test checks this page against the command's own help, so it lists every command and option
there is.

**Set up**: [init](#brainrc-init) · [import](#brainrc-import) · [new pack](#brainrc-new-pack) ·
[new skill](#brainrc-new-skill) · [new agent](#brainrc-new-agent) · [new rule](#brainrc-new-rule) ·
[new command](#brainrc-new-command) ·
**Install**: [status](#brainrc-status) · [apply](#brainrc-apply) · [update](#brainrc-update) · [install](#brainrc-install) · [uninstall](#brainrc-uninstall) ·
**Check**: [check](#brainrc-check) · [audit](#brainrc-audit) · [scope](#brainrc-scope) · [doctor](#brainrc-doctor) · [validate](#brainrc-validate) · [tokens](#brainrc-tokens) ·
**Other**: [pin-mcp](#brainrc-pin-mcp) · [migrate](#brainrc-migrate)

## brainrc init

First run: pick the tools to manage, adopt your existing instruction files, and choose how much
to install. It writes `harnesses.local.toml`, `packs.local.toml` and `brainrc.local.toml`, and never runs `apply`
([getting started](getting-started.md#1-choose-what-to-install-optional)).

| Option | Does |
|---|---|
| `--yes`, `-y` | ask nothing: manage every installed tool and adopt every instruction file |
| `--harness HARNESS` | manage exactly these tools (`--harness claude,codex`, or repeat it); asks nothing |
| `--no-adopt` | leave your instruction files where they are |
| `--profile minimal\|recommended\|full` | set the profile ([configuration](configuration.md#brainrclocaltoml)) |
| `--starter minimal\|app\|infra` | set a starter profile instead: rules only; no infrastructure skills; everything |
| `--import` | import this folder's CLAUDE.md, AGENTS.md, Cursor, Copilot and Windsurf files and Claude Code plugin into the pack `imported` without asking |
| `--dry-run` | print what `init` would do, write nothing |

## brainrc import

Turn instruction files you already have, or a Claude Code plugin, into a pack: one rule per
section, in order ([packs](packs/import.md)). `--format` takes `instructions`, `cursor`,
`copilot`, `windsurf` or `plugin`.

```bash
brainrc import ~/.claude/CLAUDE.md --name mine --enable
```

| Option | Does |
|---|---|
| `PATH ...` | files or folders to import, in order |
| `--to DIR` | where to write the pack (default `$BRAINRC_HOME/imported/<name>`) |
| `--name NAME` | the pack's name (default `imported`) |
| `--prefix PREFIX` | the prefix for its skills, agents, commands and MCP servers (default `<name>-`) |
| `--format FORMAT` | read every PATH as this format, whatever its name |
| `--force` | replace an earlier pack in that folder |
| `--enable` | add the pack to `packs.local.toml` |
| `--dry-run` | print the files it would write, write nothing |

## brainrc new pack

Start a pack of your own that validates on its first run: `pack.toml`, a README, an `AGENTS.md`
for whoever edits it, a first rule, a facts skill, tripwires, tests, a CI workflow, a pre-commit
config and a `.gitignore` ([packs](packs.md#what-new-pack-writes)). In a terminal it asks for what you
don't give it; otherwise it takes the defaults. A folder that holds only `.git`, such as a fresh
clone, counts as empty. Then it checks the pack as `validate --pack` does.

```bash
brainrc new pack acme
brainrc validate --pack acme
```

| Option | Does |
|---|---|
| `NAME` | the pack's name (asked for in a terminal) |
| `--to DIR` | where to write it (default `./<name>`) |
| `--prefix PREFIX` | the prefix for its items (default `<name>-`, or `<owner>-` with `--id`) |
| `--id OWNER/PACK` | the ID it is published under ([naming](packs.md#naming)) |
| `--description TEXT` | one line on what the pack is for |
| `--harness HARNESS` | the tools you'll edit it with: `claude` adds a `CLAUDE.md`, `gemini` a `GEMINI.md`, each pointing at `AGENTS.md` (default: every enabled tool) |
| `--ticket none\|github\|jira\|local` | the ticket system Gatework uses for the pack's refs (default `none`) |
| `--refs REF,...` | the ticket refs it handles, such as `ACME-*` (default: from the ticket system) |
| `--host HOST` | with `--ticket jira`: the Jira site, such as `acme.atlassian.net` |
| `--yes`, `-y` | ask nothing: take the defaults |
| `--force` | replace an earlier pack in that folder; its `.git` stays |
| `--enable` | add the pack to `packs.local.toml` |
| `--dry-run` | print the files it would write, write nothing |

## brainrc new skill

Write a skill in the pack you are in (the nearest folder from here up with a `pack.toml`), or the
one `--pack` names: `skills/<prefix><name>/SKILL.md` with its `name` and `description`
([packs](packs.md#what-new-item-writes)). Then it checks the pack as `validate --pack` does.

```bash
brainrc new skill deploy --description "Deploy acme services. Use when asked to ship one."
brainrc new skill protobuf --domain '*.proto,buf.yaml'
```

| Option | Does |
|---|---|
| `NAME` | the skill's name; the pack's prefix is added when it's missing (asked for in a terminal) |
| `--pack DIR` | the pack to write it in (default: the nearest folder from here up with a `pack.toml`) |
| `--description TEXT` | what it does and when to use it (asked for in a terminal; a domain skill has one by default) |
| `--domain GLOB,...` | the files it is for: a domain skill with Validate (offline), Conventions, Review checklist and Never without approval sections, and a `[[extensions.gatework.domains]]` row in `pack.toml` |
| `--yes`, `-y` | ask nothing: take the defaults |
| `--force` | replace a skill of that name |
| `--dry-run` | print the files it would write, write nothing |

## brainrc new agent

Write an agent in the pack you are in: `agents/<prefix><name>.md` with its `name`, `description`,
read-only `tools` and `model`, and a Handoff section with the block it ends with.

| Option | Does |
|---|---|
| `NAME` | the agent's name; the pack's prefix is added when it's missing |
| `--pack DIR` | the pack to write it in (default: the nearest folder from here up with a `pack.toml`) |
| `--description TEXT` | when to delegate to it (asked for in a terminal) |
| `--tools TOOL,...` | its tools (default `Read, Grep, Glob`); add `Edit`, `Write` or `Bash` only when it needs them |
| `--model MODEL` | `haiku`, `sonnet`, `opus`, `inherit` or a full ID (default `inherit`) |
| `--yes`, `-y` | ask nothing: take the defaults |
| `--force` | replace an agent of that name |
| `--dry-run` | print the files it would write, write nothing |

## brainrc new rule

Write a rule in the pack you are in: `rules/NN-<name>.md`, numbered after the pack's last rule
(rounded up to the next ten, so there is room for one between), with the frontmatter core's rules
carry. Then it prints what the rule adds to every session and what the pack now loads against its
`max_always_tokens` budget.

| Option | Does |
|---|---|
| `NAME` | the rule's name, after its number |
| `--pack DIR` | the pack to write it in (default: the nearest folder from here up with a `pack.toml`) |
| `--yes`, `-y` | ask nothing |
| `--dry-run` | print the file it would write, write nothing |

A rule of the same name is refused: it never replaces one.

## brainrc new command

Write a command in the pack you are in: `commands/<prefix><name>.md` with its `description` and
`$ARGUMENTS`. Codex skips commands that use `$ARGUMENTS`, so when brainrc manages Codex it offers
the user-invoked skill form instead, `skills/<prefix><name>/SKILL.md` with
`disable-model-invocation: true` ([formats](formats.md#commands-commandsnamemd)), which every tool runs.

| Option | Does |
|---|---|
| `NAME` | the command's name; the pack's prefix is added when it's missing |
| `--pack DIR` | the pack to write it in (default: the nearest folder from here up with a `pack.toml`) |
| `--description TEXT` | one line shown in the command picker (asked for in a terminal) |
| `--as-skill` | write the user-invoked skill form |
| `--as-command` | write `commands/<prefix><name>.md` without asking |
| `--argument-hint TEXT` | what to type after the command, shown in the picker |
| `--yes`, `-y` | ask nothing: take the defaults |
| `--force` | replace a command of that name |
| `--dry-run` | print the files it would write, write nothing |

## brainrc status

Show what `apply` would change, for this machine and for the project you are in. Writes nothing.
The words it prints are explained in [getting started](getting-started.md#2-preview).

| Option | Does |
|---|---|
| `--only HARNESS` | only these tools (`--only claude,codex`, or repeat it) |
| `--repair` | also show the links `apply --repair` would fix |

## brainrc apply

Render rules, link items into each tool, and merge hooks and MCP servers into its settings. Then,
in a repo with `brainrc.toml`, write the project's files. Keeps each git pack at its locked commit.

| Option | Does |
|---|---|
| `--only HARNESS` | only these tools; the others are left exactly as they are |
| `--repair` | also relink links left broken by moving a clone or upgrading brainrc |
| `--yes`, `-y` | accept new hooks, MCP servers, tool grants and network domains from packs without asking. Without it, `apply` asks, and refuses where it can't ask (CI, a pipe) |

## brainrc update

Move git packs to what their `ref` points at now. It prints the commits and files that change,
then runs `apply` and relocks. This is the only command that moves a pin ([team setup](project.md#pinned-commits-and-update)).

| Option | Does |
|---|---|
| `PACK ...` | the packs to move (default: every git pack) |
| `--yes`, `-y` | accept new permissions without asking, as for `apply` |

## brainrc install

Without `--frozen`, the same as `apply`. With `--frozen`, install exactly what `brainrc.lock`
records, or fail and write nothing. For CI and teammates ([team setup](project.md#installing-from-the-lock)).

| Option | Does |
|---|---|
| `--frozen` | install exactly what the lock records |
| `--scope user\|project` | which lock `--frozen` installs (default: the project's when there is one) |
| `--force` | with `--frozen` in a project: overwrite files at the lock's paths that brainrc didn't write |
| `--yes`, `-y` | as for `apply`; not with `--frozen`, where the lock is the approval |

## brainrc uninstall

Remove everything `apply` put into your tools: links, hooks, MCP servers, and the folders that
leaves empty. Your own settings stay, and an instructions file `init` moved aside is put back.

| Option | Does |
|---|---|
| `--dry-run` | print what would be removed, remove nothing |
| `--purge` | also delete the settings home: local config, rendered files and fetched packs |

## brainrc check

Exit 1 when the packs or the repo's agent files differ from `brainrc.lock`, naming each
difference. No network, writes nothing. Made for CI ([team setup](project.md#checking-for-drift-in-ci)).

| Option | Does |
|---|---|
| `--scope user\|project` | which lock to check (default: the project's when there is one) |

## brainrc audit

List every skill, agent, command, rule, hook and MCP server each tool loads from brainrc, with
the pack it came from, the pack's commit and the item's hash. Then each pack's permissions and
each MCP server's pinned tools. No network, writes nothing ([guardrails](guardrails.md#auditing-what-agents-load)).

| Option | Does |
|---|---|
| `--json` | print it as JSON |

## brainrc scope

List each enabled pack as `APPLIES` or `SKIPPED` in the directory you're in, and why: the git
remote, directory, kube context, AWS profile or ticket ref that matched its `[scope]`, or what it
needs. A pack without `[scope]` applies everywhere. Writes nothing ([packs](packs.md#scope)).

| Option | Does |
|---|---|
| `--cwd DIR` | check this directory instead of the current one |
| `--ticket REF` | a ticket ref the run is for (repeat it); the branch name's refs count too |
| `--extensions` | print `extensions.md` with only the packs that apply here |
| `--json` | print it as JSON |

## brainrc doctor

Check this machine's install: stale rules, missing or broken links, packs not fetched, hooks that
can't run, a plugin installed twice. Prints each problem with its fix and exits 1 if there is
one. Changes nothing. No options.

## brainrc validate

Check every source: frontmatter, links and references, pack names, collisions, `requires_core`,
token budgets and tripwires. CI runs it on brainrc itself; pack authors run it with `--pack`
([packs](packs/validate-in-ci.md)).

| Option | Does |
|---|---|
| `--pack DIR` | check core plus this pack only, and run the pack's own tests |
| `--fetch-defaults` | with `--pack`: check it against the default packs at the versions core pins, fetched into separate clones |
| `--local-tripwires FILE` | read local tripwire terms from FILE instead of `tripwires.local.toml`; FILE must exist and list a term (CI writes it from a secret) |

## brainrc tokens

Estimate the context cost of each skill, agent and command: what loads in every session and what
loads on use. No options ([packs](packs.md#context-cost)).

## brainrc pin-mcp

Start each stdio MCP server brainrc installs for Claude Code, list its tools, and on your yes
record a hash of each one. A hook then warns at session start when a pinned tool changes
([MCP servers](mcp.md#pin-their-tools)).

| Option | Does |
|---|---|
| `SERVER ...` | the servers to pin (default: every one) |
| `--yes`, `-y` | approve new and changed tool definitions without asking |

## brainrc migrate

Move the old settings home from before the rename (`~/.config/ai-config` or `$AICFG_HOME`) to
`~/.config/brainrc` (or `$BRAINRC_HOME`), then run `apply`. Refuses a target that isn't empty ([upgrading](upgrade.md#from-ai-config)).

| Option | Does |
|---|---|
| `--dry-run` | only print the move |

## Exit codes

`0` on success. `1` when a command found a problem: a `CONFLICT`, a failed check, drift, or
an error in a config file. `2` for a usage error, such as an unknown option.
