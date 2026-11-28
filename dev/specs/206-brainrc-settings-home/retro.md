# Retro: 206-brainrc-settings-home

Ticket: gh:206 (also closes #131) · Size: standard · PR: https://github.com/brainrc/brainrc/pull/232

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | see state.json `metrics` (gate times recorded) |
| Time per stage | see `metrics.stage_started_at` |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 8 (T1-T6, F1, F2), sequential |
| Review first-pass rate | T1, T2 first pass; T4 needed a second attempt (1 HIGH from code review) |
| Retries | 1 (T4) |
| Interventions | 1 (spec amended after approval: XDG + legacy-only) |
| Criteria passed | 16/16 |

## Reflections
1. skipped
2. The approved spec skipped the legacy fallback when XDG_CONFIG_HOME was set; the engine caught it reading T2's diff, and the owner chose to amend.
3. skipped

## Proposed improvements
- analyst role: when a spec has an ordered lookup with a fallback, state each fallback's condition against every earlier rule and check it against the resolved questions; here question 2 and the paragraph disagreed.
- A minor changelog fragment should also check `examples/pack-acme`'s `requires_core` (the 0.4.0 break fixed in #231); consider a validate rule.
- Data-moving commands deserve a security review by default; it found the `AICFG_HOME=$HOME` deletion path.

## After delivery
- Outcome: merged
- Merged at: 2026-10-28T05:02:24Z · Time to merge: 7 min
- Post-merge verify: pass (see `verify-merged.md`)
- CI failures: 1 own (CI runners set `XDG_CONFIG_HOME`; a pre-existing test isolated only `HOME`) / 0 external
- Review rounds: 0
- Caught by reviewers, missed by the run's own: CI caught the XDG test leak; the run's verify never set `XDG_CONFIG_HOME`
- Follow-up title: none
- Follow-up body: none
