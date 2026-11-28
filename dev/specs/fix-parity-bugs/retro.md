# Retro: fix-parity-bugs

Ticket: local · Size: standard · PR: https://github.com/bxker/ai-config/pull/57

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 3 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 5/5 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? A second implementation diffed against the first
   found crashes the unit tests never reached; a differential run is a cheap bug hunt.

## Notes
- The hook-order test uses 8 new events so a lucky set order can't pass it by chance.
