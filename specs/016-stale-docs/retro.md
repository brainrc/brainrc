# Retro: 016-stale-docs

Ticket: gh:16 · Size: small (resized from standard) · PR: https://github.com/bxker/ai-config/pull/30

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | about 30m wall clock, almost all waiting at the Spec gate |
| Time per stage | spec (incl. gate wait), implement 3m, verify 1m |
| Gate rework (spec / plan / deliver) | 0 / skipped / 0 |
| Tasks | 1 |
| Review first-pass rate | n/a (inline) |
| Retries | 0 |
| Interventions | 1 (resize to small) |
| Criteria passed | 5/5 |

## Reflections
1. Did the result match what you meant? Not asked yet.
2. Where did you have to step in, and why? Resizing: the file-count signal scored a three-line
   docs fix as `standard`.
3. One change that would have prevented that? Below.

## Proposed improvements
- `sizing.md`: score "files touched" by changed lines as well. A few lines across 3 docs
  files should land at `small`. Same root cause as the 007 retro, so this is now seen twice.
