# Retro: 101-reject-duplicate-pack-names

Ticket: gh:101 · Size: small · PR: https://github.com/brainrc/brainrc/pull/222

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:19 to the stack Deliver approval, of which 1 min waiting at gates (this child's gates plus the shared stack gate) |
| Time per stage | recorded starts: intake 02:26Z, spec 02:26Z, implement 02:30Z, verify 02:30Z, document 02:30Z, deliver 02:30Z (later stages of inline runs share one timestamp) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 1 (no parallel waves: inline mode) |
| Review first-pass rate | 0/1 (0%) |
| Retries | 0 |
| Interventions | 0 |
| Review context | n/a (inline) |
| Criteria passed | 4/4 |

## Reflections
Asked once for campaign gh:93 at delivery; answers recorded here if given.
1. skipped (not answered yet)
2. skipped (not answered yet)
3. skipped (not answered yet)

## Proposed improvements
- Back-filled the Spec approval time with its presented time, then removed it: the engine should record `approved_at` in the same step that reads the answer, before any other work.
- Fallback mode for standard children: the role agents aren't installed in this cloud session, so reviews ran shared. Installing them (`python3 scripts/aicfg.py apply` in the session image, or a SessionStart hook) would allow fresh-context reviews.
