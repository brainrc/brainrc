# cli-entry-points

How the tool is installed and invoked, and how deprecated names behave.

### brainrc command
The system SHALL install as distribution `brainrc` with console script `brainrc`, import package
`brainrc`, `python -m brainrc`, `scripts/brainrc.py`, and `--version`, with usage text naming
`brainrc`. (AC1, AC2, AC4, AC6, AC8, AC9)
_Last changed by 205-brainrc-package-command._

### Deprecated aicfg names
The system SHALL keep the `aicfg` console script, `scripts/aicfg.py`, `python -m aicfg`, and
`import aicfg` working through one minor release, each warning (on stderr / as a
`DeprecationWarning`) and otherwise behaving as `brainrc`. (AC3, AC5, AC6, AC7, AC11)

Existing living requirements mention `aicfg` commands by name; their wording is left to #209.
_Last changed by 205-brainrc-package-command._
