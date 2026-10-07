# Spec: spec-agent retro improvements (round 2)

Ticket: gh:44 · Size: small (4 files, ~15 lines) · Status: draft

## Problem
Five process gaps showed up across the last four runs; each cost a fix cycle or a near miss.

## Acceptance criteria
- **AC1** `agents/verifier.md`: when the change adds or alters something a person runs (a
  command, script, or documented steps), the verifier runs it once for real in a scratch copy
  and records what it printed; a fake home is a fresh empty directory, never removed through
  a variable like `$HOME`.
- **AC2** `agents/implementer.md`: when the code under test already exists, red is shown by
  disabling only the new change, never by stashing or reverting whole files.
- **AC3** `references/lifecycle.md` deliver: the done checkpoint is pushed only after CI on the
  delivered commit finishes, so delivery is one push while CI runs.
- **AC4** `references/sizing.md`: test lines count about half toward changed lines, like new
  self-contained docs.
- **AC5** VERSION 0.3.10 with a CHANGELOG entry; `validate` and tests pass.

## Design choice
Test lines count half (not zero): tests are lower risk than the code they cover, but a large
test diff still takes review time.

## Open questions
None.
