# cli-entry-points

How the tool is installed and invoked, and how deprecated names behave.

### brainrc command
The system SHALL install as distribution `brainrc` with console script `brainrc`, import package
`brainrc`, `python -m brainrc`, `scripts/brainrc.py`, and `--version`, with usage text naming
`brainrc`. (AC1, AC2, AC4, AC6, AC8, AC9)
_Last changed by 205-brainrc-package-command._

### Old names live only in an allowlist
The system SHALL name itself `brainrc` in all user-facing text, and SHALL keep `aicfg`/`ai-config` only in a test-enforced allowlist of compatibility spots. (AC1, AC2, AC3, AC4)
_Last changed by 209-brainrc-docs-wording._

### Old-name support window is published
The changelog SHALL state, as a **[pack contract]** note, which old names 0.5.0 removed and what replaces each. (AC8)
_Last changed by 238-remove-deprecated-names._

### Command-line parsing
`brainrc` SHALL parse its commands with argparse: `--help` (top level and per command) and `--version` SHALL exit 0, usage errors SHALL exit 2 on stderr, help SHALL name the installed command or the checkout script, and the maintainer commands `plugin` and `release` SHALL run but stay out of the command list. (AC1, AC2, AC3, AC4, AC5)
_Last changed by 125-argparse-cli._

### Sync only some harnesses
`brainrc status` and `brainrc apply` SHALL take `--only <harness>` (repeatable or comma-separated) and SHALL then plan, link, prune and merge settings and MCP servers for those harnesses only, leaving every other harness and the shared hooks copy as they are; a name that isn't an enabled harness SHALL exit 2 and write nothing. (AC6, AC7)
_Last changed by 125-argparse-cli._
