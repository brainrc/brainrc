# Retro: 050-aicfg-home

Ticket: gh:50 (step 1) · Size: standard · PR: https://github.com/bxker/ai-config/pull/52

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 3 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 7/7 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? The real upgrade run found the emptied `dist/`
   left behind; tests now cover it.

## Notes
- The Plan gate's `approved_at` was not captured when the owner clicked Approve; it repeats
  `presented_at`. The Deliver approval time was captured with `date -u` right after the click.
  With button gates, record `approved_at` in the first command after the answer.
