# run-lifecycle

Stages, gates, and state a spec-agent run moves through.

### Watch stage for CI failures
For `delivery: normal` runs on a connector with `pr_status`, `stage` SHALL pass through `watch` between `deliver` and `done`; resuming at `watch` SHALL handle changes since `watch.checked_at`; a failed check SHALL be recorded as `external` (also red on base, or naming nothing in the diff) and stop with a note, or as `own` and fixed through a `C` task with the normal retry budget; `local-only` runs and connectors without `pr_status` SHALL skip `watch`. (AC1, AC2, AC3, AC4, AC5, AC6)
_Last changed by 079-watch-ci-failures._

### Push gate
A run SHALL NOT push a watch fix without approval at a Push gate showing diff stat, commits, and the check it should fix. (AC7)
_Last changed by 079-watch-ci-failures._

### Post-deliver state
`state.json` SHALL record `watch.checked_at`, `watch.ci_failures`, and `metrics.post_deliver_retries`, documented in `state.md`. (AC8)
_Last changed by 079-watch-ci-failures._
