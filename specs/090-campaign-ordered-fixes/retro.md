# Retro: 090-campaign-ordered-fixes

Ticket: gh:90 · Size: standard · PR: https://github.com/bxker/ai-config/pull/91

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 1:30 total = 0:17 agent + 1:13 waiting at gates |
| Time per stage | spec 1, plan 1, implement 15 (incl. review and fixes), verify <1 (verify and document share one timestamp) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 6 (T1-T4, fixes F1-F2; no parallel waves, fallback mode) |
| Review first-pass rate | 1/2 (50%) |
| Retries | 1 |
| Interventions | 0 |
| Review context | fresh (fresh-context subagent, user's choice) |
| Criteria passed | 10/10 |

## Reflections
1. skipped (asked at delivery; answers to be recorded if given)
2. skipped
3. skipped

## Proposed improvements
- `fallback.md` § Review isolation: offer a fresh-context general-purpose subagent as the default when the harness has one, instead of only "new session" or "shared"; it gave an independent review without a session switch and caught a real HIGH.
- Mode detection: Claude Code with a generic subagent tool but no named roles could run reviewers that way (role file + dispatch prompt), keeping writers inline.
