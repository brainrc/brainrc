# Spec: Copy hooks into AICFG_HOME

Ticket: gh:99 · Size: standard · Status: approved

## Problem
With `aicfg` installed as a package (`uv tool install` / `pipx`), the hooks dir link points into
the package: `.../lib/python3.X/site-packages/_core/overrides/<harness>/hooks`. When an upgrade
moves the tool to a new Python, that path is gone. Since gh:98 the guards then fail open:
Claude Code keeps working, but every guard is silently off until the user re-runs `aicfg apply`
(and only `doctor` says so). Hooks are the one linked item whose loss removes protection, so
they must not depend on a versioned package path.

## Goals
- An installed `aicfg`'s hooks keep working across `uv tool upgrade` / `pipx upgrade`, even
  when the Python version changes, without re-running `apply`.
- A checkout keeps today's behavior: hooks link into the checkout, so edits take effect at once.

## Non-goals
- Skills, agents, commands, and the OpenCode `plugin.js` links into the package. They also
  dangle after a Python change, but losing them blocks nothing; `doctor` and `apply` fix them.
  A follow-up can copy those too.
- Pack hooks (packs live in local dirs or `$AICFG_HOME` fetches, not in the package).
- Updating the copy automatically on upgrade: the copy is refreshed by the next `apply`.

## Acceptance criteria
- **AC1**: Given an installed `aicfg` (core under `_core`), when `aicfg apply` runs, then every
  core `overrides/<harness>/hooks/` dir is copied to `$AICFG_HOME/hooks/core/<harness>/hooks/`
  (all of them, since Cursor's guard runs Claude's guards from the sibling dir), and each enabled
  harness's `hooks_dir` link points at its copy, not into the package.
- **AC2**: Given that install, when the package directory is removed or moved (an upgrade to a
  new Python), then the Claude Code and Cursor guard commands still run the guards: a risky
  Bash call still gets `ask` (Claude) / `deny` (Cursor).
- **AC3**: Given the installed package's hooks changed (an upgrade), when `aicfg status` runs,
  then it reports the hooks copy as needing an update, and `aicfg apply` replaces the copy
  (no leftover files from the old version), after which status is in sync.
- **AC4**: Given a checkout (not installed), when `aicfg apply` runs, then hooks still link
  into `overrides/<harness>/hooks` of the checkout and nothing is copied.
- **AC5**: Given an existing installed setup whose `hooks_dir` links into the package, when
  `aicfg apply` runs after this change, then the link is re-pointed at the copy (reported as an
  update, not a conflict), and `aicfg doctor` reports no problem with it.
- **AC6**: Given a harness is disabled, when `aicfg apply` runs, then its hooks link is removed
  as today. Given every harness with a `hooks_dir` is disabled, then `$AICFG_HOME/hooks/core/`
  is removed too.

## Constraints
- Stdlib only. `aicfg status` stays read-only (no copy, no `$AICFG_HOME` writes).
- The copy is replaced atomically enough that a running guard never sees a half-copied dir
  (copy to a sibling temp dir, then swap).
- Keeps gh:98's fail-open commands and doctor hook check working against the copy.

## Requirement changes

### Area: aicfg-apply
#### ADDED: Installed hooks live in AICFG_HOME
When `aicfg` runs from an installed package, `aicfg apply` SHALL copy core's hooks to
`$AICFG_HOME/hooks/core/<harness>/hooks/` and link `hooks_dir` there, refresh the copy when the
package's hooks change, and remove it when no harness with hooks is enabled. From a checkout, hooks SHALL
stay linked into the checkout. (AC1, AC2, AC3, AC4, AC5, AC6)

## Open questions
None. Resolved at the Spec gate: Q1 copy only when installed (AC1, AC4).
Revision 1 (found at plan): the copy holds every core hooks dir, because Cursor's guard runs
Claude's guards from `<root>/claude/hooks`; AC1 and AC6 changed to match.
