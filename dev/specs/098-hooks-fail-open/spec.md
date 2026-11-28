# Spec: Hooks fail open when their file is missing

Ticket: gh:98 · Size: standard · Status: approved

## Problem
ai-config's guard hooks run as `python3 "<hooks dir>/<guard>.py"`, and the hooks dir is a link
into the checkout (or site-packages). When that target goes away (checkout moved or deleted,
package removed, Python upgraded), `python3` can't open the file and exits 2. Claude Code reads
exit 2 from a PreToolUse hook as "block", so every Bash, Read, Write, Edit, and MCP call is
refused and the user is locked out of their own harness until they edit `settings.json` by hand.
`aicfg doctor` doesn't notice.

## Goals
- A missing hook file never blocks the harness: the guard is skipped, the tool call runs.
- `aicfg doctor` reports each missing or broken ai-config hook with the fix.

## Non-goals
- Moving hooks out of the checkout or site-packages (gh:99).
- Pack hook commands: pack authors write their own fragments. Doctor still checks them when they
  follow the `python3 "<hooks dir>/<file>.py"` shape.
- Warning inside the harness at session start that a guard is missing.
- OpenCode (its guards are a JS plugin, not a hook command).

## Acceptance criteria
- **AC1**: Given `aicfg apply` merged ai-config's Claude Code hooks, when the hooks dir's target
  is deleted and the hook command runs (through `sh -c`, as Claude Code runs it) with a
  PreToolUse payload on stdin, then it exits 0 with no output (the tool call proceeds).
- **AC2**: Given the hook file exists, when the hook command runs, then it behaves exactly as the
  guard does today (same exit code and output for a risky and a safe call).
- **AC3**: Given Cursor's hooks are merged and the hooks dir's target is deleted, when a Cursor
  hook command runs, then it exits 0 and prints `{"permission": "allow"}`.
- **AC4**: Given ai-config's hooks are in a harness's settings file and a hook's script file is
  missing, when `aicfg doctor` runs, then it reports a FAIL `<harness>: hook missing: <path>`
  with `aicfg apply` (or the checkout's apply command) as the fix, and exits non-zero.
- **AC5**: Given a hook's script exists but exits non-zero for an empty `{}` payload (broken
  install, syntax error), when `aicfg doctor` runs, then it reports a FAIL naming the hook and
  its exit code.
- **AC6**: Given a healthy install, when `aicfg doctor` runs, then it reports no hook findings,
  and every hook it ran got `{}` on stdin with a timeout of the hook's own `timeout` (default 5s).
- **AC7**: Given existing installs, when `aicfg apply` runs after upgrading, then the old-form
  hook groups are replaced by the new ones (no duplicate guards).

## Constraints
- Security trade-off: failing open means a missing guard silently stops guarding. Accepted by the
  ticket; doctor (AC4) is how users find out. Needs security review.
- Hook commands run under `sh` on macOS, Linux, and Git Bash on Windows: POSIX `sh` syntax only.
- Doctor stays read-only: running a guard with `{}` writes nothing.
- New guard patterns aren't added, so `tests/test_hooks.py` needs no risky/near-miss pair; the
  fail-open tests go there.

## Requirement changes

### Area: aicfg-apply
#### ADDED: Hooks fail open
ai-config's hook commands SHALL exit 0 without blocking (Cursor: with an allow response) when
their script file is missing, and behave as the guard otherwise. (AC1, AC2, AC3, AC7)
#### ADDED: Doctor checks hooks
`aicfg doctor` SHALL report each ai-config hook in a harness's settings file whose script is
missing, or that exits non-zero for an empty payload, with the fix. (AC4, AC5, AC6)

## Open questions
None. Resolved at the Spec gate: Q1 a missing Cursor guard prints `{"permission": "allow"}` (AC3). Fail-open trade-off accepted.
