# Retro: 050-codex

Ticket: gh:50 (step 2) · Size: standard · PR: https://github.com/bxker/ai-config/pull/53

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | gate timestamps in state.json |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 |
| Retries | 0 |
| Interventions | 0 |
| Criteria passed | 6/6 |

## Reflections
1. Did the result match what you meant? (ask the owner)
2. Where did you have to step in, and why? (ask the owner)
3. One change that would have prevented that? Installing the real Codex CLI found both
   problems (skipped `$ARGUMENTS` commands, dropped symlinks); the spike's source reading
   missed the second. Install the real tool in the spike next time.

## Notes
- Removing core `commands/` broke the test fixture that copied it; `SOURCES` now leaves it out.
- Codex hooks and rules remain unverified; they need a logged-in session with the owner's OK.
