Rebuild the CLI on argparse, with --only for status and apply

Part of epic #109 (E4), 1 of 6. Closes #125.

## Why
`brainrc --help` was a usage error, no command had its own help, and there was no way to sync one harness without touching the rest. The next E4 parts (`init`, `uninstall`, `apply --repair`) need real subcommands and options.

## What changed
- The CLI is built on argparse. `--help`, `<command> --help` and `--version` exit 0. A bad command or option prints usage to stderr and exits 2.
- `plugin` and `release` still run but no longer appear in the command list.
- Help names `brainrc <command>` when installed and `python3 scripts/brainrc.py <command>` in a checkout.
- `status` and `apply` take `--only <harness>` (repeat it, or `--only claude,codex`). Only those harnesses are linked, pruned and merged. The others keep their links, hooks and MCP servers, and the installed hooks copy is never pruned under `--only`. An unknown or disabled name exits 2 and writes nothing.
- docs/install.md mentions `--help` and `--only`.

## Acceptance criteria
- [x] AC1: `--help`, `-h`, `--version` exit 0. Verified by `HelpTest`.
- [x] AC2: every command has its own `--help`. Verified by `HelpTest`.
- [x] AC3: `plugin` and `release` are hidden and still run. Verified by `HelpTest`.
- [x] AC4: usage errors exit 2 on stderr. Verified by `HelpTest` and `BrainrcCommandTest`.
- [x] AC5: help names the installed command or the script. Verified by `HelpTest` and `InstalledModeTest`.
- [x] AC6: `apply --only claude` touches only Claude; other harnesses keep their state. Verified by `OnlyTest` and `OnlyInstalledTest`.
- [x] AC7: a bad `--only` name exits 2 and writes nothing. Verified by `OnlyTest`.

## How to verify
```
python3 -m unittest tests.test_cli_args
python3 -m unittest discover -s tests
python3 scripts/brainrc.py --help
python3 scripts/brainrc.py status --only claude
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Campaign, Spec, Plan, Deliver. See `specs/125-argparse-cli/log.md`.
- A harness outside `--only` is left alone even if it is disabled. Its cleanup waits for a full `apply`, so `--only` never removes anything outside its scope.
- `apply --only` still renders rules and pack extensions, since every harness reads them.
- `--version` together with a command is a usage error rather than silently ignoring the command.
- `help` and `bogus` used to print the usage text to stdout with exit 2. Two existing tests now check `--help` (exit 0) and stderr instead.

## Follow-ups
- None.

Spec: `specs/125-argparse-cli/spec.md` · Plan: `specs/125-argparse-cli/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
