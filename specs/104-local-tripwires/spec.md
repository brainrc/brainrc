# Spec: Keep core employer-neutral, mechanically

Ticket: gh:104 · Size: small · Status: approved

## Problem
Core issues, code, docs, specs and the changelog must never name a pack's employer or clients.
Today that rests on memory: `tripwires.toml` exists only for packs, and a maintainer can't list
their own forbidden terms without committing them, which would leak the very names it guards.

## Goals
- Each maintainer lists their own forbidden terms in a gitignored `tripwires.local.toml`.
- `validate`, and so the pre-commit hook, fails when any tracked core file holds one of them.
- The file itself can never be committed by accident.

## Non-goals
- Scanning git history, issues or PR text (only the tracked tree).
- Pack tripwires (`tripwires.toml` in a pack) and their allow patterns (#210).
- A CI step: CI has no local file, so the check is a no-op there by design.

## Acceptance criteria
- **AC1**: Given `tripwires.local.toml` with `terms = ["initech"]`, when any tracked core file
  (any type, not only markdown) contains "Initech" in any case, then `validate` exits 1 and names
  `<file>:<line>` and the term; a term in a tracked file's path fails the same way.
- **AC2**: Given no `tripwires.local.toml`, or terms found nowhere, then `validate` passes as before.
- **AC3**: Given a git checkout, when a file with a term is untracked, then it is not checked;
  once staged it is. Per-machine `*.local.*` files are never checked.
- **AC4**: Given `tripwires.local.toml` is tracked by git, then `validate` fails and says how to
  untrack it; the repo's `.gitignore` ignores the file.
- **AC5**: Given a malformed file (`terms` not a list of non-empty strings, or bad TOML), then
  `validate` fails with a message and no traceback.
- **AC6**: Given AGENTS.md and CONTRIBUTING.md, when read, then they say how to list terms.

## Constraints
Stdlib only. No new dependency. Existing `tripwires.toml` behavior unchanged.

## Requirement changes
### Area: validate
Purpose: What `brainrc validate` checks in core and in packs beyond item frontmatter.
#### ADDED: Local tripwires
`brainrc validate` SHALL read an optional, gitignored `tripwires.local.toml` (`terms = [...]`) at
the core root and fail on every tracked core file whose path or text contains a term, compared
case-insensitively, naming the file, line and term; it SHALL fail when that file is tracked, and
SHALL skip untracked and per-machine `*.local.*` files. (AC1, AC2, AC3, AC4, AC5)

## Open questions
None. Defaults taken under `--oneshot`:
1. Terms are literal and case-insensitive, not regexes: a maintainer lists names, and a literal
   can't be mistyped into a pattern that matches everything.
2. Without git (an installed copy), every file outside dot-directories is checked instead.
3. The error names the term: the output is local, and the maintainer needs it to fix the file.

## Proposed split
