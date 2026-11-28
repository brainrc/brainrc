Fail validate on a maintainer's local tripwire terms

Part of epic #94 (E3), 1 of 3. Closes #104.

## Why
Core must never name a pack's employer or clients, but nothing checked it. A maintainer couldn't list their own forbidden names in the repo without committing the very names they want to keep out.

## What changed
- `brainrc validate` reads an optional `tripwires.local.toml` at the repo root (`terms = ["..."]`). Any tracked core file whose path or text contains a term fails, ignoring case, with `<file>:<line>` and the term. Binary files are skipped.
- Only files git tracks (the index, so staged files count at pre-commit time) are checked; without git it walks the tree like the pack tripwires do. Per-machine `*.local.*` files are never checked.
- `validate` fails if `tripwires.local.toml` itself is ever tracked. `.gitignore` already ignores it (`*.local.toml`), and a test pins that.
- A malformed file (bad TOML, or `terms` not a list of non-empty strings) fails with a message, not a traceback.
- AGENTS.md and CONTRIBUTING.md say how to use it.

## Acceptance criteria
- [x] AC1: a term in any tracked core file, or in its path, fails validate with file, line and term. Verified by `LocalTripwireTest`.
- [x] AC2: no file, or no hits, changes nothing. Verified by `LocalTripwireTest` and `ValidateTest.test_repo_is_valid`.
- [x] AC3: untracked and `*.local.*` files are skipped; a staged file is checked. Verified by `LocalTripwireTest` with `git init`.
- [x] AC4: a tracked `tripwires.local.toml` fails; the repo ignores it. Verified by `LocalTripwireTest`.
- [x] AC5: malformed files fail without a traceback. Verified by `LocalTripwireTest`.
- [x] AC6: AGENTS.md and CONTRIBUTING.md document it.

## How to verify
```
python3 -m unittest tests.test_brainrc.LocalTripwireTest
python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
printf 'terms = ["Initech"]\n' > tripwires.local.toml && python3 scripts/brainrc.py validate; rm tripwires.local.toml
```
(The last line fails on purpose: the docs and tests use "Initech" as the example term.)

## Decisions made without you
- Gates auto-approved (`--oneshot`): Campaign, Spec, Deliver. See `specs/104-local-tripwires/log.md`.
- Terms are literal and case-insensitive, not regexes, so a typo can't turn into a pattern that matches everything.
- The error message names the term. The output only ever runs locally, and you need the term to fix the file.
- `.pre-commit-config.yaml` is unchanged: its `brainrc-validate` hook already runs on every commit and now reads the file.
- The examples use the fictional "Initech", not "acme": core is full of "acme", so it can't be the example of a forbidden term.

## Follow-ups
- **You:** create your own `tripwires.local.toml` with your employer's and clients' names.

Spec: `specs/104-local-tripwires/spec.md` · Plan: `specs/104-local-tripwires/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
