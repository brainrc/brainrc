# Retro: 069-deliver-owner-quiz

Ticket: gh:69 · Size: standard · PR: https://github.com/bxker/ai-config/pull/85

## Metrics
| Metric | Value |
|---|---|
| Duration (intake → deliver) | 13:03 total = 11:50 agent + quiz answers + idle, 1:13 waiting at gates (wall clock; the session sat idle for long stretches) |
| Time per stage | not split: verify and document started from the same timestamp |
| Gate rework (spec / plan / deliver) | 0 / 0 / 1 |
| Tasks | 9 (T1–T5, F1–F4; no parallel waves) |
| Review first-pass rate | 1/3 (33%) |
| Retries | 0 |
| Interventions | 2 |
| Understanding (asked / first try / after explanation / rounds) | 5 / 3 / 2 / 9 |
| Review context | fresh (reviews and examiner ran as fresh subagents; the engine ran in fallback) |
| Criteria passed | 12/12 |

## Reflections
1. skipped
2. skipped
3. skipped

## Proposed improvements
- The quiz format changed twice during the Deliver quiz: free text, then a pick plus a why, then multiple choice. Show a sample question at the Spec gate so the owner can try the format before it's built.
- Free-text grading and the pick-plus-why version each needed a full review cycle. When an owner changes a design mid-gate, list the affected criteria and files before editing.
- `deliver-diff.patch` picked up a local ticket file's status line; exclude ticket files from it.
- Wire `metrics.understanding` into the metrics rollup (deferred follow-up).
