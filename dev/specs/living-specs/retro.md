# Retro: living-specs

Ticket: gh:23 · Size: standard · PR: https://github.com/bxker/ai-config/pull/65

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 06:14 → 06:31 UTC (gate timestamps in state.json) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 + 1 review fix |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 6/6 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? Running the new template through the new parser
   (the F1 finding) belongs in T1: a test that feeds the template's own text to the script.

## Notes
- Sequential sandbox runs need run 1 merged to main, which `main_untouched` reports; a
  two-run eval case would need its own check for that.
