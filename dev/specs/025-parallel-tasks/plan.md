# Plan: Parallel implement waves in subagent mode

Inline mode. One review pass over the whole diff before Verify.

| Task | What | Files | Criteria | Red test |
|---|---|---|---|---|
| T1 | Engine and contract docs: "Parallel waves" note; Implement stage waves and landing; `after:`; state fields; retro line | `skills/spec-agent/references/efficiency.md`, `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/state.md`, `skills/spec-agent/templates/plan.md`, `skills/spec-agent/templates/retro.md`, `agents/architect.md` | AC1–AC3 | n/a (prose); `validate` checks links and frontmatter |
| T2 | Sandbox ticket 003, eval case, README row; test that every eval case's `ticket_ref` names a ticket that exists in `examples/sandbox/` | `examples/sandbox/tickets/003-two-features.md`, `examples/sandbox/README.md`, `evals/cases/sandbox-003.toml`, `tests/test_evals.py` | AC4 | new test fails once the case exists and the ticket doesn't |
| T3 | Real landing run in a scratch repo (two worktrees, ordered landing, stray-file rejection) recorded in verify.md; VERSION 0.3.13; CHANGELOG | `VERSION`, `CHANGELOG.md` | AC5, AC6 | `validate` |

## Risks
- `SKILL.md` and `efficiency.md` are always read by the engine: keep the additions short; the
  detail lives in the efficiency note. Check `aicfg tokens` before and after.
