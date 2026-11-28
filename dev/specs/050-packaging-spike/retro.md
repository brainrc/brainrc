# Retro: 050-packaging-spike

Ticket: gh:50 (spike) · Size: small · PR: https://github.com/bxker/ai-config/pull/51

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json (research ran before intake) |
| Gate rework (spec / plan / deliver) | 0 / skipped / 0 |
| Tasks | 1 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 4/4 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? Researchers cloned repos outside the working
   directory; research prompts should say "clone only into the scratchpad".

## Notes
- `metrics.gates.spec.approved_at` was first written as an estimate; corrected below to the
  time recorded at the done checkpoint. Timestamps must come from `date -u`, never estimated.
