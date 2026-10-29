# Spec: Remove the deprecated aicfg names in 0.5.0

Ticket: local:specs/tickets/238-remove-deprecated-names.md · Size: standard · Status: approved

## Problem
Since 0.4.0 every old name has warned "removed in 0.5.0". These names are the `aicfg` console script,
`scripts/aicfg.py`, `python -m aicfg`, `import aicfg`, the `aicfg_home` alias, `AICFG_HOME` and the
legacy `~/.config/ai-config` home. The check from 236 blocks a `minor` bump while they exist. If the old
home were simply no longer read, `apply` would run against an empty new home and drop every pack the
user had set up, with no error.

## Goals
- Release 0.5.0 with the deprecated names gone and `SHIM_REMOVED_IN` removed.
- A user with an unmigrated old home gets an error that names `brainrc migrate`, never a silent reset.

## Non-goals
- On-disk convergence from 207 and 237 (hook dirs, MCP markers, guard link, fetch record, backups):
  it stays.
- `brainrc migrate` and doctor's old-plugin warning: they stay.

## Acceptance criteria
- **AC1**: Given the built wheel, then its console scripts are only `brainrc`, and it holds no `aicfg`
  package. Given a checkout, then `scripts/aicfg.py` and `aicfg/` don't exist, and CI does not call them.
- **AC2**: Given `brainrc.config`, `brainrc.cli` or `brainrc`, then `aicfg_home`, `SHIM_REMOVED_IN`,
  `warn_deprecated` and `warn_home` don't exist, and no command prints a deprecation line.
- **AC3**: Given `AICFG_HOME` set, `BRAINRC_HOME` unset, and the new home absent or empty, when
  `brainrc status`, `apply` or `update` runs, then it writes nothing, prints
  `ERROR AICFG_HOME is no longer read: set BRAINRC_HOME=<new home> and run brainrc migrate`, and exits 1.
- **AC4**: Given only a legacy `~/.config/ai-config` (the new home is absent), when `status`, `apply`
  or `update` runs, then it writes nothing, prints an `ERROR` naming the old dir and
  `brainrc migrate`, and exits 1. Given the new home exists, then the old dir is ignored, as today.
- **AC5**: Given either case from AC3 or AC4, then `brainrc migrate` still moves the old home and the
  next `apply` succeeds. `doctor` reports a FAIL with the migrate fix. `validate`, `doctor`, `migrate`,
  `plugin` and `--version` run without the error.
- **AC6**: Given `skills/spec-agent/scripts/active_run.py`, then it resolves only `BRAINRC_HOME`,
  absolute `$XDG_CONFIG_HOME/brainrc`, or `~/.config/brainrc`.
- **AC7**: Given `examples/pack-acme/pack.toml`, `docs/packs.md` and `docs/tutorial.md`, then
  `requires_core` admits 0.5 (`<0.6`), and `validate --pack examples/pack-acme` passes on 0.5.0.
- **AC8**: Given the fragment `changelog.d/238-remove-deprecated-names.md`, then it bumps `minor`
  and has a **[pack contract]** bullet naming what was removed and what replaces each. `validate`
  passes, and the 236 removal-release check passes because `SHIM_REMOVED_IN` is gone.
- **AC9**: Given tests/test_old_names.py, then rows exist only for names still in the code. The suite
  passes with and without `XDG_CONFIG_HOME`, and `scripts/check_install.py` no longer checks `aicfg`.

## Constraints
- Stdlib only.
- Docs drop "keeps working until 0.5.0" wording and point upgrades at `brainrc migrate`.

## Requirement changes
### Area: cli-entry-points
#### REMOVED: Deprecated aicfg names
Why: removed in 0.5.0, as the deprecation warnings announced.
#### MODIFIED: Old-name support window is published
The changelog SHALL state, as a **[pack contract]** note, which old names 0.5.0 removed and what replaces each. (AC8)
### Area: aicfg-config
#### MODIFIED: Settings home
The system SHALL resolve its settings home by the order above, defaulting to `~/.config/brainrc`,
and SHALL NOT read the legacy `~/.config/ai-config` or `AICFG_HOME`; while either holds an unmigrated
home, `status`, `apply` and `update` SHALL write nothing and exit 1 with an error naming `brainrc migrate`. (AC3, AC4, AC5)
### Area: aicfg-apply
#### MODIFIED: Doctor reports an unmigrated home
`brainrc doctor` SHALL report a FAIL, with the migrate fix, when the legacy dir or `AICFG_HOME` holds an
unmigrated home, and SHALL warn when an unused old dir remains. (AC5)

## Open questions
1. What happens to an unmigrated old home? *Default taken:* `status`, `apply` and `update` refuse and
   name `brainrc migrate`. Silently starting fresh would drop every pack.
2. Keep the 236 removal-release check once `SHIM_REMOVED_IN` is gone? *Default taken:* yes. It is off
   while the constant is absent, so the next deprecation can reuse it.
3. Does the CI step that runs `validate --pack examples/pack-acme` stay? *Default taken:* yes, through
   `scripts/brainrc.py`. If a step already does this, the deprecated one is just removed.

## Proposed split
Not applicable.
