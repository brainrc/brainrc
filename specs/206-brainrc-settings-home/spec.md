# Spec: Settings home ~/.config/brainrc and BRAINRC_HOME

Ticket: gh:206 (epic #199, 3 of 6) · Size: standard · Status: approved

## Problem
Local files (`packs.local.toml`, `harnesses.local.toml`, `rules/*.local.md`, git packs, rendered
instructions and extensions, the hooks copy, `active-run`) live in `~/.config/ai-config`, named by
`AICFG_HOME`, which ignores `XDG_CONFIG_HOME` (#131). After the #205 rename the tool is `brainrc`
but its home still says `ai-config`. Existing installs must keep working, be told to move, and have
a safe way to move.

## Goals
- A new default home `~/.config/brainrc`, overridable by `BRAINRC_HOME` and `XDG_CONFIG_HOME`.
- Old-only installs keep working and warn; `brainrc migrate` moves them; doctor reports leftovers.

## Non-goals
- Owned hooks dir names, MCP ownership file names, backup suffix (#207); plugin namespace (#208);
  docs wording beyond what this change makes wrong (#209).
- Removing `AICFG_HOME` support (goes with the `aicfg` shims, `SHIM_REMOVED_IN`).
- Merging two homes. Touching the real HOME: all tests use a temp HOME.

## Acceptance criteria
Home is resolved in this order: `BRAINRC_HOME`; `AICFG_HOME`; `$XDG_CONFIG_HOME/brainrc` (when set
and absolute); `~/.config/brainrc`; except that if neither `BRAINRC_HOME` nor `AICFG_HOME` is set
and the new home (`$XDG_CONFIG_HOME/brainrc` or `~/.config/brainrc`) is absent but
`~/.config/ai-config` exists, the latter is used ("legacy").

- **AC1**: Given a temp HOME with no old or new dir and no env vars, when `brainrc apply` runs, then
  files are rendered under `~/.config/brainrc`, `~/.config/ai-config` is not created, and nothing
  is warned about the home.
- **AC2**: Given `BRAINRC_HOME=X` and `AICFG_HOME=Y` both set, then `X` is used and `Y` is ignored.
- **AC3**: Given `XDG_CONFIG_HOME=X` (absolute) and no `BRAINRC_HOME`/`AICFG_HOME`, then
  `X/brainrc` is used; unset (or empty or relative) it falls back to `~/.config/brainrc`. If
  `X/brainrc` is absent and `~/.config/ai-config` exists, the legacy dir is used and warns (AC4).
- **AC4**: Given only `~/.config/ai-config` exists (no env vars), when `brainrc status` or `apply`
  runs, then that dir is used, it works as before, and stderr has one line naming the legacy dir
  and `brainrc migrate`; stdout is unchanged and the exit code is unaffected.
- **AC5**: Given `AICFG_HOME=Y` and no `BRAINRC_HOME`, then `Y` is used and stderr has one line
  naming `BRAINRC_HOME`. The warning appears once per invocation, never on stdout, and not for
  `--version`.
- **AC6**: Given both `~/.config/brainrc` and `~/.config/ai-config` exist, then the new dir is
  used, the old one is never read, and commands other than `doctor` do not warn.
- **AC7**: Given a legacy install with links into the old dir, when `brainrc migrate` runs, then
  the old dir's contents (including git packs' working trees, `packs.local.toml`,
  `harnesses.local.toml`, `rules/*.local.md`) are in the new dir byte-for-byte, the old dir is gone,
  `apply` then re-runs, and no symlink under the temp HOME points into the old dir (the
  instructions links point at the new render).
- **AC8**: Given the new dir exists and is non-empty (or `BRAINRC_HOME` points at a non-empty
  dir), when `migrate` runs, then it exits non-zero, names both dirs, and changes nothing. An
  existing empty target is accepted.
- **AC9**: Given `migrate --dry-run`, then it prints what would move and where, writes nothing, and
  exits 0 (non-zero in the AC8 situation).
- **AC10**: Given no old dir (already migrated, or a new install), when `migrate` runs, then it
  prints that there is nothing to migrate, changes nothing, and exits 0; repeated runs after a
  successful migrate are no-ops.
- **AC11**: Given `AICFG_HOME` set and `BRAINRC_HOME` unset, when `migrate` runs, then it exits
  non-zero telling the user to move to `BRAINRC_HOME` (or unset `AICFG_HOME`), and changes nothing.
  With `BRAINRC_HOME` set, the source is `AICFG_HOME` if set, else `~/.config/ai-config`.
- **AC12**: Given another `apply` holds the lock, when `migrate` runs, then it exits non-zero and
  moves nothing.
- **AC13**: Given the move succeeded but the follow-up `apply` fails, then `migrate` exits
  non-zero, says the move is done and to run `brainrc apply`.
- **AC14**: Given a legacy-only install or `AICFG_HOME` in use, when `doctor` runs, then it
  reports a WARN naming the dir and the fix `brainrc migrate`. Given both dirs exist, it reports a
  WARN that the old dir is unused and can be removed. Given only the new dir, no home finding.
- **AC15**: Given `skills/spec-agent/scripts/active_run.py`, then `write` and `read` use the same
  resolution order and legacy fallback (own copy of the logic, stdlib only), and print no
  deprecation line.
- **AC16**: Given the test suite, then every case above runs against a temp HOME, and
  `python3 -m unittest discover -s tests` and `python3 scripts/brainrc.py validate` pass.

## Constraints
- Stdlib-only Python 3.11+; offline. Home resolution is read-only (never creates or moves anything).
- The `apply` lock, hooks copy, `mcp-owned.json`, and `opencode/agents` follow the resolved home.
- Docs naming `~/.config/ai-config` or `AICFG_HOME` as the default (install.md, packs.md,
  formats.md, spec-agent state.md/SKILL.md) are updated only where now wrong.

## Requirement changes
### Area: aicfg-config
#### ADDED: Settings home
The system SHALL resolve its settings home by the order above, defaulting to `~/.config/brainrc`,
use a legacy `~/.config/ai-config` or `AICFG_HOME` only as a fallback with a once-per-run stderr
warning, and never prefer the old dir when the new one exists. (AC1 to AC6)
#### ADDED: Migrate
`brainrc migrate` SHALL move the old home to the new one, re-run apply so no link points into the
old dir, refuse a non-empty target, support `--dry-run`, and be idempotent. (AC7 to AC13)
### Area: aicfg-apply
#### MODIFIED: Installed hooks live in AICFG_HOME
When `brainrc` runs from an installed package, `brainrc apply` SHALL copy core's hooks to
`<settings home>/hooks/core/<harness>/hooks/` and link `hooks_dir` there, refresh the copy when
the package's hooks change, and remove it when no harness with hooks is enabled. From a checkout,
hooks SHALL stay linked into the checkout. (AC1, AC7)
#### ADDED: Doctor reports an unmigrated home
`brainrc doctor` SHALL warn, with the fix, when the legacy dir or `AICFG_HOME` is in use or an
unused old dir remains. (AC14)
### Area: run-pointer
#### MODIFIED: Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to
`active-run` in the settings home (default `~/.config/brainrc/active-run`) at intake, on every
resume, and on every checkpoint commit (each gate, block, and done), creating the directory if
needed, via `skills/spec-agent/scripts/active_run.py write`. A write failure SHALL warn on stderr
and exit 0. In an ordered campaign the pointer SHALL name the child currently in progress. (AC15)

## Open questions
Resolved at the Spec gate (owner took every recommended default):
1. `XDG_CONFIG_HOME` is folded in; this change closes #131.
2. With `XDG_CONFIG_HOME` set, the legacy dir is still `~/.config/ai-config`.
3. `migrate` refuses while `AICFG_HOME` is set and `BRAINRC_HOME` is not (AC11).
4. Doctor rates legacy use as WARN.
5. `migrate` never merges or overwrites (AC8).
6. `active_run.py` is silent on the legacy fallback (AC15).
7. A symlinked old dir is moved as the link itself; its target is left alone.

## Proposed split
Not applicable (standard).
