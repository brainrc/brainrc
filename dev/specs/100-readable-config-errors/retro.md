# Retro: 100-readable-config-errors

Ticket: gh:100 · Size: standard · PR: https://github.com/brainrc/brainrc/pull/221

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 0:36 to the stack Deliver approval, of which 2 min waiting at gates (this child's gates plus the shared stack gate) |
| Time per stage | recorded starts: intake 02:10Z, spec 02:10Z, plan 02:11Z, implement 02:14Z, verify 02:25Z, document 02:25Z, deliver 02:26Z (later stages of inline runs share one timestamp) |
| Gate rework (spec / plan / deliver) | 0 / 0 / 0 |
| Tasks | 5 (no parallel waves: fallback mode) |
| Review first-pass rate | 1/2 (50%) |
| Retries | 0 |
| Interventions | 0 |
| Review context | shared |
| Criteria passed | 8/8 |

## Reflections
Asked once for campaign gh:93 at delivery; answers recorded here if given.
1. skipped (not answered yet)
2. skipped (not answered yet)
3. skipped (not answered yet)

## Proposed improvements
- Review finding (HIGH) caught an off-by-one in end-of-document TOML error lines; the first test hit a different tomllib branch. implementer role: when a helper has branches keyed on a library's message format, drive one test through each branch and assert the branch's own text.
- Fallback mode for standard children: the role agents aren't installed in this cloud session, so reviews ran shared. Installing them (`python3 scripts/aicfg.py apply` in the session image, or a SessionStart hook) would allow fresh-context reviews.
