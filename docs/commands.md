# Commands

Every `brainrc` command and option. `brainrc --help` lists the commands and
`brainrc <command> --help` shows one command's options. From a clone, run
`python3 scripts/brainrc.py <command>` instead. `brainrc` with no command runs `status`, and
`brainrc --version` prints the version.

A test checks this page against the command's own help, so it lists every command and option
there is.

**Set up**: [init](#brainrc-init) · [import](#brainrc-import) ·
**Install**: [status](#brainrc-status) · [apply](#brainrc-apply) · [update](#brainrc-update) · [install](#brainrc-install) · [uninstall](#brainrc-uninstall) ·
**Check**: [check](#brainrc-check) · [audit](#brainrc-audit) · [doctor](#brainrc-doctor) · [validate](#brainrc-validate) · [tokens](#brainrc-tokens) ·
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
| `--import` | import this folder's CLAUDE.md, AGENTS.md, Cursor and Copilot files into the pack `imported` without asking |
| `--dry-run` | print what `init` would do, write nothing |

## brainrc import

Turn instruction files you already have into a pack: one rule per section, in order
([packs](packs.md#import)).

```bash
brainrc import ~/.claude/CLAUDE.md --name mine --enable
```

| Option | Does |
|---|---|
| `PATH ...` | files or folders to import, in order |
| `--to DIR` | where to write the pack (default `$BRAINRC_HOME/imported/<name>`) |
| `--name NAME` | the pack's name (default `imported`) |
| `--prefix PREFIX` | the prefix for its skills (default `<name>-`) |
| `--format FORMAT` | read every PATH as this format, whatever its name |
| `--force` | replace an earlier pack in that folder |
| `--enable` | add the pack to `packs.local.toml` |
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

## brainrc doctor

Check this machine's install: stale rules, missing or broken links, packs not fetched, hooks that
can't run, a plugin installed twice. Prints each problem with its fix and exits 1 if there is
one. Changes nothing. No options.

## brainrc validate

Check every source: frontmatter, links and references, pack names, collisions, `requires_core`,
token budgets and tripwires. CI runs it on brainrc itself; pack authors run it with `--pack`
([packs](packs.md#validate-a-pack-in-its-own-ci)).

| Option | Does |
|---|---|
| `--pack DIR` | check core plus this pack only, and run the pack's own tests |
| `--fetch-defaults` | with `--pack`: check it against the default packs at the versions core pins, fetched into separate clones |

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
