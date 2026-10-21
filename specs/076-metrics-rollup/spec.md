# Spec: Metrics rollup across spec-agent runs

Ticket: gh:76 · Size: standard · Status: draft

## Problem
Each spec-agent run records metrics in `state.json` and `retro.md`, but nothing reads them across runs. There is no baseline, so the owner cannot tell whether a change to a role or rule helped. Later post-deliver fields (`watch`, outcomes, understanding, session tokens) also need a place to land. Older runs lack newer fields, so any rollup must distinguish "unknown" from zero.

## Goals
- One offline command reports per-run and aggregate metrics over runs under one or more roots.
- Output is readable by people (text) and stable for tools (JSON).
- Optional cost data from ccusage, with clean degradation when it is absent.

## Non-goals
- New fields in `state.json`, or changes to what the engine records.
- The `watch` stage, outcome measures, or the session-token mod.
- Writing to run folders, or fixing bad timestamps in old runs.
- Installing or requiring ccusage.

## Acceptance criteria
- **AC1**: Given Python 3.11+ with no third-party packages, when `scripts/retro_report.py --help` runs, then it exits 0 and prints usage covering `--root`, `--json`, and `--ccusage`.
- **AC2**: Given no `--root`, when it runs, then it scans `./specs/*/state.json`; given `--root` repeated, it scans every root and reports each run once with its root identified.
- **AC3**: Given runs under several roots, when the report is produced, then it lists every run and an aggregate across all of them: runs by size, by mode, and by final stage (done / in progress / blocked).
- **AC4**: Given a run with `metrics.gates.*` and `stage_started_at`, when reported, then it shows total duration split into gate wait (sum of `approved_at - presented_at`) and agent time (total minus wait), plus time per stage with gate waits excluded.
- **AC5**: Given a complete run, when reported, then it shows gate rework per gate, review first-pass rate (`first_pass/total`), retries, interventions, and wave stats (task-minutes against wall-minutes) when `metrics.waves` exists.
- **AC6**: Given an old-format run missing a field (e.g. no `metrics.gates`, no `waves`), when reported, then that value shows as unknown and is excluded from averages and totals, never counted as 0.
- **AC7**: Given a `state.json` that is unreadable, invalid JSON, or not an object, when the report runs, then that run is listed as skipped with the reason, the others still report, and the exit code is 0.
- **AC8**: Given an in-progress or blocked run, when reported, then it appears with its stage and `blocked` reason, and its not-yet-reached values are unknown.
- **AC9**: Given `--json`, when run, then stdout is a single JSON document with a `schema_version`, per-run records (with `null` for unknown), skipped runs with reasons, and aggregates; the schema is documented in `docs/`.
- **AC10**: Given `--ccusage` and ccusage not installed or failing, when run, then the report completes with cost columns `n/a` and a note that cost is unavailable; without `--ccusage`, ccusage is never invoked.
- **AC11**: Given `--ccusage` and ccusage output (faked in tests), when run, then token and cost data are merged into the report and JSON.
- **AC12**: Given fixture runs (complete, old-format, in-progress, malformed) in `tests/`, when `python3 -m unittest discover -s tests` runs, then the new tests pass without network or ccusage.
- **AC13**: Given the docs, when read, then they explain how to run the script, what each number means, and the JSON schema, and the roadmap item is marked Done.

## Constraints
- Stdlib only, Python 3.11+, offline; read-only on run folders.
- Output must not embed absolute home paths beyond what the user passed as `--root`.
- Existing runs show inconsistent timestamps (see question 2), so no crash on negative or out-of-order values.

## Requirement changes

### Area: metrics-report
Purpose: Aggregate spec-agent run metrics across projects.
#### ADDED: Run discovery and tolerance
The system SHALL find runs under one or more roots, report each, treat missing fields as unknown (never zero), and skip malformed runs with a reason without failing the rest. (AC2, AC6, AC7, AC8)
#### ADDED: Per-run and aggregate metrics
The system SHALL report size, mode, final stage, duration split into agent time and gate wait, time per stage, gate rework, review first-pass rate, retries, interventions, wave stats, and criteria passed. (AC3, AC4, AC5)
#### ADDED: Text and JSON output
The system SHALL print a text table by default and a documented, versioned JSON document with `--json`. (AC9)
#### ADDED: Optional ccusage cost
The system SHALL merge ccusage token and cost data only when `--ccusage` is given and ccusage works, else show cost as `n/a`. (AC10, AC11)

## Open questions
1. "Criteria passed" has no field in `state.json` (tasks list criteria, not results). Is `retro.md`'s `Criteria passed` row the only source, and may the script parse that markdown row? *Matters: the retro format becomes a parsed contract; unknown when absent.*
2. `specs/012-aicfg-doctor/state.json` has `approved_at` earlier than `presented_at` (plan gate) and out-of-order `stage_started_at`. Should such gates be flagged as invalid and excluded, or clamped? *Matters: negative waits would skew totals.*
3. How does ccusage data map to a run (by date range from `started_at` to `done`, or by project/session)? Which ccusage command and output format is assumed? *Matters: attribution is the only way cost can be per-run, and the format can't be verified here.*
4. Duration for in-progress runs: use now, last stage start, or unknown? *Matters: affects averages.*
5. Should `mode`, `size`, and rework averages include skipped/in-progress runs? *Matters: definition of the aggregate denominators.*
