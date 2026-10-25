# metrics-report

Aggregate spec-agent run metrics across projects.

### Run discovery and tolerance
The system SHALL find runs under one or more roots, report each, treat missing fields as unknown (never zero), skip malformed runs with a reason without failing the rest, and flag invalid timestamps with a warning and exclude them from totals. (AC2, AC6, AC7, AC8, AC18)
_Last changed by 024-metrics-rollup._

### Per-run and grouped aggregate metrics
The system SHALL report duration, gate rework, first-pass rate, retries, interventions, wave stats, and criteria passed as before, and also outcome, post-merge result, time to merge, review rounds, and CI failures per run, with average time to merge and merged, abandoned, and regression counts in the aggregates, missing values unknown. (AC8)
_Last changed by 081-watch-post-merge._

### Markdown and JSON output
The system SHALL print a Markdown table by default and a documented, versioned JSON document with `--json`. (AC10, AC11)
_Last changed by 024-metrics-rollup._

### Optional ccusage tokens and cost
The system SHALL report period-total tokens and cost from `ccusage daily --json` only when `--ccusage` is given and works, else tokens unknown and cost `n/a`. (AC12, AC13, AC14)
_Last changed by 024-metrics-rollup._
