# Spec: CI matrix, lint and types

Ticket: gh:147 (epic #113, 2 of 4) · Size: standard · Status: approved

## Problem
CI runs `validate.yml` on ubuntu with Python 3.12 only. Regressions on other Pythons (3.11, 3.13)
or on macOS go unseen, and nothing proves the tutorial's commands still work. `docs/install.md`
(Platforms) states macOS and Linux are supported and Windows needs WSL, because install and
spec-agent's `roles` link rely on symlinks. The ticket asks for ubuntu/macOS/Windows x 3.11/3.12/3.13,
ruff, pyright, coverage on PRs, and the tutorial run in CI.

## Goals
- Every existing validate step runs on ubuntu and macOS across Python 3.11, 3.12 and 3.13.
- The tutorial's commands are checked in CI using the standard library only.
- Windows results are visible without claiming Windows support.

## Non-goals
- Adding ruff, pyright or coverage.py (new third-party tools need owner approval; see Open questions).
- Making brainrc work natively on Windows, or changing `docs/install.md` Platforms.
- Weakening, skipping or deleting any test or check to get a cell green.
- Changing the CLI, hooks, release workflow, or the `check_install.py` contract.

## Acceptance criteria
- **AC1**: Given a push to main or a PR, when `validate.yml` runs, then a job matrix covers
  os {ubuntu, macOS, Windows} x python {3.11, 3.12, 3.13} (9 cells) with `fail-fast` off.
- **AC2**: Given each ubuntu and macOS cell, when it runs, then it executes `validate`, `validate --pack
  examples/pack-acme`, the full unittest suite, the pip-install smoke (`check_install.py`) and the
  sandbox tests, with the same commands as today.
- **AC3**: Given the matrix, when it runs, then the gitleaks scan runs exactly once (one ubuntu cell),
  since it downloads a linux binary; no other check is dropped from any cell it can run in.
- **AC4**: Given the Windows cells, when a step fails, then the cell is reported but does not fail the
  workflow (`continue-on-error`), a comment in the workflow says why, and a follow-up issue is named
  in the PR description. No step is skipped or weakened on Windows.
- **AC5**: Given `docs/tutorial.md`, when a stdlib-only check script runs in CI (ubuntu and macOS
  cells), then it executes the tutorial's `brainrc` commands (validate, pack validate, `status`,
  `apply`, in-sync check) against a temporary HOME and pack directory, and fails with the step name
  when one exits non-zero or its documented output (`OK:`, `Everything in sync.`) is missing.
- **AC6**: Given the check script, when the tutorial's commands change without the script changing,
  then a test in `tests/` fails (the script reads its commands from the doc, not a copy).
- **AC7**: Given the PR, when it is opened, then ruff, pyright and coverage are not added, and the PR
  description lists them as a follow-up needing owner approval, so "coverage reported on PRs" is
  not met by this change.
- **AC8**: Given the repo, when `python3 scripts/brainrc.py validate` and the unittest suite run
  locally, then both pass; the PR carries a `changelog.d/` fragment.

## Constraints
Stdlib only for `brainrc/`, hooks and the new script (Python 3.11+). Action pins stay by commit SHA
with version comments. Existing `timeout-minutes` and `permissions: contents: read` stay. macOS and
Windows cells can only be observed after push; offline evidence is a local ubuntu run plus a YAML
read-through.

## Requirement changes
### Area: ci
Purpose: What the validate workflow must prove on every push and PR.
#### ADDED: Cross-platform validate matrix
The validate workflow SHALL run the repo's checks on ubuntu and macOS for Python 3.11, 3.12 and 3.13 with fail-fast off, run gitleaks once, and report Windows cells without letting them fail the workflow. (AC1, AC2, AC3, AC4)
#### ADDED: Tutorial is executed in CI
CI SHALL run an executable check derived from `docs/tutorial.md` and fail when a documented command fails or its documented output is missing. (AC5, AC6)

## Open questions
1. Ticket says "green on all 9 cells", but Windows is documented unsupported (symlinks, `python3` in
   hook commands). *Matters: the done-when cannot honestly be met.* Safe default: Windows is
   non-blocking (AC4); promoting it to required is a follow-up once it passes.
2. Add ruff, pyright and coverage.py? *Matters: new dependencies need owner approval, and "coverage
   reported on PRs" depends on it.* Safe default: no (AC7); follow-up issue. A stdlib `trace` report
   is not offered as a substitute.
3. Should tutorial check cover steps 6-7 (reads `~/.claude`, `tokens`)? *Matters: scope and
   fragility.* Safe default: only steps 1, 2, 4, 5.

## Proposed split
None.
