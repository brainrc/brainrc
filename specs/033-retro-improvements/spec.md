# Spec: Apply the first five retros to spec-agent

Ticket: gh:33 · Size: standard · Status: approved

## Problem
Five runs on this repo hit the same friction: small docs tickets scored `standard` and got an
extra gate, the Deliver gate made code changes look missing, parallel release PRs conflicted on
`VERSION`, retro timings mixed agent time with waiting for the user, a message contradicting the
docs got past review, and fallback mode ran silently. Each cost the user a gate, an
intervention, or a merge fix.

## Goals
- Fewer gates and interventions on small or repetitive tickets, with the same safety.
- Retros that measure agent time separately from waiting.

## Non-goals
- Automating any of this in `aicfg.py`. These are instructions to the engine and roles.
- Changing the Spec/Plan/Deliver gate model or the size floors.

## Acceptance criteria
- **AC1**: `sizing.md` scores changed lines alongside files: a change of roughly ≤ 30 lines
  with no design choice is at most `small` even across 3+ files, and new self-contained
  example or doc files count lighter than edits to existing code. The floors still win.
- **AC2**: The Deliver gate format (`lifecycle.md` § Gate presentation) lists changed files
  outside `specs/` with a diff stat before the spec artifacts.
- **AC3**: At intake, when the repo keeps a `VERSION` file, the engine lists other open PRs
  that change `VERSION` or `CHANGELOG.md` and recommends waiting for them to merge, or says
  this run's version must be set after they land. The same check runs again before Deliver.
- **AC4**: `state.json` records `metrics.gates.<gate>.presented_at` and `approved_at` (UTC,
  from `date -u`), and `retro.md` reports agent time and gate wait time separately.
- **AC5**: `code-reviewer` checks that user-facing text the diff adds (messages, errors,
  warnings, help) agrees with the docs the diff or repo has.
- **AC6**: At intake, when the harness could run subagents but the named agents aren't
  installed, the engine says it's running in fallback and points to `aicfg apply`.
- **AC7**: Edits stay short (references load on demand, the code-reviewer loads per review).
  `validate` and tests pass. `VERSION` bumped per policy with a CHANGELOG entry.

## Constraints
Docs only. Keep `state.json` changes backward-compatible: resume must still work on runs
without the new fields.

## Open questions
1. **Line threshold for AC1?** Default: ~30 changed lines, stated as a guide not a hard rule.
   *Matters because* too high skips the Plan gate on real design work.
2. **Version?** Default: PATCH (`0.3.1`). Engine instructions change, but no `pack.toml`
   key, rendered extension, or validate rule changes, so packs are unaffected.
3. **Where does AC3 get open PRs?** Default: through the ticket connector's system (GitHub:
   `gh pr list` or MCP `list_pull_requests`), skipped with a one-line note when unavailable.
