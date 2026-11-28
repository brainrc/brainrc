# Plan: brainrc uninstall

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** additive: new `uninstall` command.
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** removes links, hook groups and MCP entries brainrc owns; `--purge` deletes `$BRAINRC_HOME`. Rewritten or emptied files are kept as backups.

## Approach
New `brainrc/uninstall.py` plans a list of steps, prints them, and runs them unless `--dry-run`.
Harness configs are the manifest's (#126) plus harnesses.toml's, so paths survive a broken or
changed config. Roots are the manifest's recorded roots plus the current sources. Links are the
symlinks in each harness's kind dirs, instructions and plugin paths and the hooks dir's parent
whose target `plan._managed_target` recognises, which works for dangling links. Settings use a
`SettingsMerge` with no fragments, and MCP a `McpSync` with no servers: the same code paths a
disabled harness already takes in apply. A result with nothing of the user's left is renamed to
a backup. An instructions path gets `init`'s newest backup back. Empty directories are found by
simulating the removals, stopping at the harness home. `cli.py` adds the subparser and runs it
under the same `apply.lock` as apply.

## Files
| File | Change |
|---|---|
| `brainrc/uninstall.py` | new |
| `brainrc/cli.py` | modify: `uninstall` subparser, a shared `_locked` helper |
| `brainrc/__init__.py` | modify: export `uninstall` |
| `docs/troubleshooting.md`, `docs/install.md` | modify: the Uninstall section uses the command |
| `tests/test_uninstall.py` | new |
| `tests/test_cli_args.py` | modify: `uninstall --help` |
| `changelog.d/128-brainrc-uninstall.md` | new |

## Risks
- A link the user made by hand into the checkout's skills dir looks like brainrc's and is removed. apply already treats such links as its own.
- A harness home given only by the parent of `instructions` stays even if apply created nothing else there; it existed before apply, since #126 manages only installed harnesses.

## Test strategy
Snapshot a fake HOME (JSON parsed, backups ignored) before apply, edit after apply, uninstall, compare. Separate tests for a deleted checkout, a broken harnesses file, an unparsable settings file, init's restore, purge, dry run and a repeat run.

## Tasks
- [x] **T1** [agent: engine] uninstall command, CLI wiring, tests and docs
  - files: see Files
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7
