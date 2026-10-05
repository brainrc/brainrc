# Spec: Example pack validated in CI

Ticket: gh:7 · Size: standard · Status: draft

## Problem
Someone starting a pack has `docs/packs.md` as reference, but nothing to copy. The only working
pack lives as strings inside `tests/test_aicfg.py`. Nothing in CI proves that a documented,
realistic pack still passes `validate` after a core change, so the docs and the pack contract can
drift apart unnoticed.

## Goals
- A copyable pack in the repo that uses every documented extension point.
- The example breaks the build when a core change breaks the pack contract or the docs.

## Non-goals
- Replacing the test fixture in `tests/test_aicfg.py`.
- A pack generator or `aicfg new-pack` command.
- Tutorial prose (#13 covers that). The README stays short.

## Acceptance criteria
- **AC1**: Given `examples/pack-acme/`, when `python3 scripts/aicfg.py validate --pack
  examples/pack-acme` runs, then it passes with no errors and no warnings.
- **AC2**: The pack's `pack.toml` uses `requires_core` and every extension point documented in
  `docs/packs.md` (`domains`, `intake_context`, `ticket`, `deliver_checks`), and it contains one
  prefixed skill, one rule, one command, and a `tripwires.toml` with one tripwire.
- **AC3**: Given the pack, when someone reads its README, then it says how to copy it, rename the
  prefix, enable it in `packs.local.toml`, and validate it in the pack's own CI.
- **AC4**: Given a change that makes the example fail `validate --pack` (e.g. a core version bump
  outside its `requires_core`), when the unit tests run, then a test fails naming the problem.
- **AC5**: Given a push or PR, when the `validate` workflow runs, then it validates the example
  pack as its own step. *Verify after push: `validate` job.*
- **AC6**: `docs/packs.md` links to the example.
- **AC7**: Core `validate`, the full test suite, and enabling nothing still behave as before (the
  example is never linked or rendered unless someone lists it in `packs.local.toml`).

## Constraints
- Generic content only: "acme", reserved example domains, no real hosts or tools (AGENTS.md).
- The workflow keeps its pinned SHAs, `contents: read`, and timeout.
- No new dependencies.

## Open questions
Each has a recommended default; approving accepts them all.
1. **Hooks in the example?** Default: no `overrides/` hooks. *Matters because* enabling the
   example would then run its code on every tool call. The README points to the hooks docs.
2. **Ticket connector?** Default: core `ticket-jira` with `refs = ["ACME-*"]` and host
   `acme.example.net`, as in `docs/packs.md`. *Matters because* the connector must exist in core.
3. **Also a unit test, or only the CI step?** Default: both. A test in `tests/test_aicfg.py`
   makes local runs and pre-commit catch it, and the CI step names the failure clearly.
4. **Version bump?** Default: none. Adding an example doesn't change the pack contract. The
   CHANGELOG gets a plain (untagged) entry under an Unreleased heading.
