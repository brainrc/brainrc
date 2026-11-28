# Retro: pack-git

Ticket: gh:50 · Size: standard · PR: https://github.com/bxker/ai-config/pull/59

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 4 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 6/6 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? A test that passes before the change (the
   option-URL guard) proves nothing on its own; check each red test fails for the right reason.

## Notes
- A shallow fetch of a tag doesn't bring tags along, so `git describe` in a clone fails; fine for
  aicfg, worth knowing when debugging a pack clone.
