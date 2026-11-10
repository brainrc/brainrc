# Plan: Rebuild the CLI on argparse

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none (argparse is stdlib)
- **Public API / contract changes:** additive: `--help` per command and `--only`; `--help` now exits 0 instead of 2
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
`cli._parser()` builds an argparse parser with one subparser per command; `prog` comes from
`config.command("")`, so help names the installed command or the checkout script. Hidden commands
use `help=SUPPRESS`, and a small formatter drops them from the list. `_dispatch` maps the parsed
args to the existing `cmd_*` functions and turns argparse's `SystemExit` into a return code, so
`main()` keeps returning ints.

`--only` is a scope in `config` (`only_harnesses()` context manager, `in_scope()`), set by
`cmd_sync` around the locked sync. `plan()` filters each harness loop with it (links, disabled
cleanup, stale candidates) and `mcp_plan()` skips harnesses outside it. `_sync` skips pruning the
installed hooks copy while a scope is set, since that copy serves every hooked harness.

## Files
| File | Change |
|---|---|
| `brainrc/cli.py` | modify: argparse parser and dispatch, `cmd_sync(only=)` |
| `brainrc/config.py` | modify: harness scope, `check_only` |
| `brainrc/plan.py`, `brainrc/mcp.py` | modify: honor the scope |
| `tests/test_cli_args.py` | new |
| `tests/test_brainrc.py` | modify: usage tests now use `--help` / stderr |
| `docs/install.md` | modify: `--help` and `--only` |
| `changelog.d/125-argparse-cli.md` | new |

## Risks
- A scoped run that pruned shared state would break other harnesses: the hooks copy is the only shared thing apply prunes, and it is skipped under a scope (tested).

## Test strategy
In-process `main()` for help, errors and `--only` against a fake HOME; one subprocess test for the checkout script.

## Tasks
- [x] **T1** [agent: engine] argparse parser, `--only` scope, tests and docs
  - files: `brainrc/cli.py`, `brainrc/config.py`, `brainrc/plan.py`, `brainrc/mcp.py`, `tests/test_cli_args.py`, `tests/test_brainrc.py`, `docs/install.md`, `changelog.d/125-argparse-cli.md`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7
