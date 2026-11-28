# Retro: 005-core-version-contract

Ticket: gh:5 · Size: standard · PR: https://github.com/bxker/ai-config/pull/27

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 7:11 wall clock, mostly waiting at the Spec gate |
| Time per stage | spec 7h02 (includes gate wait), plan 3m, implement 4m, verify 1m, document 1m |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 (T1–T4, plus fix task F1) |
| Review first-pass rate | 3/3 (100%) |
| Retries | 1 (F1: warning pin contradicted the docs, found at verify) |
| Interventions | 0 |
| Criteria passed | 10/10 |

## Reflections
1. Did the result match what you meant? "yes"
2. Where did you have to step in, and why? None outside the three gates.
3. One change to a skill, agent, or rule from this run? "no"

## Proposed improvements
- `ticket-github`: it assumes the `gh` CLI. Cloud sessions have GitHub MCP tools instead, so this
  run used `git push` and MCP calls for the PR and comment. Add an "MCP equivalent" line per operation.
- Metrics: stage durations include time waiting for the user at gates. Record `gate_presented_at`
  and `gate_approved_at` so retros can separate agent time from wait time.
- Mode detection: Claude Code without these agents installed runs in fallback. The engine could
  say so at intake and point to `aicfg apply` to install them as subagents.
- `code-reviewer`: add "user-facing messages agree with the docs" to the check list. Review missed
  F1 because the message and the doc landed in different tasks.
