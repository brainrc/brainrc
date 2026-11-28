# Plan: Keep core employer-neutral, mechanically

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** none (a new optional local file; nothing changes without it)
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Add `_check_local_tripwires` to `brainrc/validate.py`, called for core only, next to the pack
`_check_tripwires`. It lists tracked files with `git -C <root> ls-files -z` (index, so staged
files count at pre-commit time) and falls back to the existing directory walk without git. Each
file's path and text lines are compared, case-folded, against the terms; binary files (a NUL in
the first 8 KiB) are skipped. The pre-commit config already runs `validate` on every commit, so
it needs no change. `.gitignore` already covers `*.local.toml`; a test pins that.

## Files
| File | Change |
|---|---|
| `brainrc/validate.py` | modify: local tripwires check |
| `tests/test_brainrc.py` | modify: `LocalTripwireTest` |
| `AGENTS.md`, `CONTRIBUTING.md` | modify: how to list terms |
| `changelog.d/104-local-tripwires.md` | new |

## Risks
- A maintainer's term that is a common word fails many files. They see every hit and can narrow it.

## Test strategy
Unit tests in `tests/test_brainrc.py` against a temp repo copy, with and without `git init`.

## Tasks
- [ ] **T1** [agent: implementer] Local tripwires in validate, with tests and docs
  - files: `brainrc/validate.py`, `tests/test_brainrc.py`, `AGENTS.md`, `CONTRIBUTING.md`, `changelog.d/104-local-tripwires.md`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6
