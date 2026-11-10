# Spec: Rebuild the CLI on argparse

Ticket: gh:125 · Size: standard · Status: approved

## Problem
The CLI is a hand-rolled `argv` match. `--help` is a usage error (exit 2), no command has its own
help, a stray option prints the whole usage text, and there is no way to sync one harness without
touching the others. The maintainer-only `plugin` and `release` commands show up for every user.
Later E4 children (`init`, `uninstall`, `apply --repair`) need real subcommands and options.

## Goals
- `brainrc --help`, `brainrc <command> --help` and `brainrc --version` exit 0.
- `status` and `apply` take `--only <harness>` and touch only those harnesses.
- `plugin` and `release` still run but are left out of the command list.
- Help reads right both from a checkout and installed.

## Non-goals
- New commands (`init`, `uninstall`, `--repair` are later children).
- `--only` for `update`, `doctor` or `validate`.
- Shell completion.

## Acceptance criteria
- **AC1**: Given any install, when the user runs `--help`, `-h` or `--version`, then it exits 0 and prints the help or `brainrc <VERSION>`.
- **AC2**: Given each user command, when run with `--help`, then it exits 0 and prints that command's own usage and options.
- **AC3**: Given the top-level help, then `plugin` and `release` are not listed, and `release --notes <VERSION>` still prints the notes.
- **AC4**: Given an unknown command or option, a missing option value, or `--version` with a command, then it exits 2 with usage on stderr and nothing on stdout.
- **AC5**: Given an installed package, then help says `brainrc <command>`; from a checkout it says `python3 scripts/brainrc.py <command>`.
- **AC6**: Given `apply --only claude` on a fresh HOME, then only `~/.claude` (and `~/.claude.json`) change; with links already made, other harnesses keep their links, hooks, MCP servers and the installed hooks copy. `--only` repeats or takes commas. `status --only` reports only those harnesses.
- **AC7**: Given `--only` naming an unknown or disabled harness, then it exits 2 with the reason and writes nothing; a broken harnesses.toml fails as it does without `--only`.

## Constraints
Stdlib only (argparse). Existing commands, arguments and exit codes for valid input are unchanged.

## Requirement changes
### Area: cli-entry-points
#### ADDED: Command-line parsing
`brainrc` SHALL parse its commands with argparse: `--help` (top level and per command) and `--version` SHALL exit 0, usage errors SHALL exit 2 on stderr, help SHALL name the installed command or the checkout script, and the maintainer commands `plugin` and `release` SHALL run but stay out of the command list. (AC1, AC2, AC3, AC4, AC5)
#### ADDED: Sync only some harnesses
`brainrc status` and `brainrc apply` SHALL take `--only <harness>` (repeatable or comma-separated) and SHALL then plan, link, prune and merge settings and MCP servers for those harnesses only, leaving every other harness and the shared hooks copy as they are; a name that isn't an enabled harness SHALL exit 2 and write nothing. (AC6, AC7)

## Open questions
None. Defaults taken under `--oneshot`:
1. A harness outside `--only` is untouched even when it is disabled: its cleanup waits for a full `apply`, so `--only` never removes anything outside its scope.
2. Rules and pack extensions are still rendered to the settings home on `apply --only`, since every harness shares them.
3. `--version` with a command is a usage error rather than ignoring the command.

## Proposed split
