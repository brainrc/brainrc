# Spec: aicfg reports these problems instead of crashing

Ticket: local (Rust parity findings) · Size: standard (4 bugs, 5 commands, tests) · Status: approved

## Acceptance criteria
- **AC1** A dangling `*.md` symlink inside a skill: `validate` exits 1 with its existing
  "dangling symlink" error and no traceback; `tokens` exits 0 and skips it.
- **AC2** An invalid `overrides/<harness>/settings.fragment.json` (core or pack), no traceback:
  - `status`/`apply`: `ERROR <file>: invalid JSON (...)`, then "Nothing written", exit 1, nothing
    written (like name collisions today).
  - `doctor`: a FAIL finding naming the file, other findings still listed.
  - `plugin`: `ERROR ...`, exit 1.
  - `validate`: the existing invalid-JSON error once (not twice, not a crash).
- **AC3** An unknown `agents_format`: `doctor` reports it as a FAIL finding (fix: use `claude` or
  `opencode`) instead of crashing; `status`/`apply` keep their current error.
- **AC4** `merge_settings` keeps existing events in place and appends new ones in fragment order,
  whatever `PYTHONHASHSEED` is.
- **AC5** Each case has a test that fails first. All tests, validates, tutorial pass; normal
  output is unchanged (same before/after diff in a fake HOME as PR #56). VERSION 0.3.21; CHANGELOG.

## Open questions
None.
