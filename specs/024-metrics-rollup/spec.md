# Spec: Metrics rollup across spec-agent runs

Ticket: gh:24 · Size: standard · Status: draft

## Problem
Each spec-agent run records metrics in `state.json` and `retro.md`, but nothing reads them across runs. `docs/efficiency.md` says to "measure against your retro.md numbers", yet there is no baseline, so the owner cannot tell whether a change to a role or rule helped. Older runs lack newer fields, so any rollup must distinguish "unknown" from zero.

## Goals
- One offline command reports per-run and aggregate metrics over runs under one or more roots, grouped by size, domain, and mode.
- Output is a Markdown table for people and a versioned JSON document for tools.
- Optional token and cost data from ccusage, with clean degradation when it is absent.

## Non-goals
- New fields in `state.json` (including a token field), or changes to what the engine records.
- The `watch` stage, outcome measures, or the session-token mod (#73).
- Writing to run folders, or fixing bad timestamps in old runs.
- Installing or requiring ccusage.

## Acceptance criteria
- **AC1**: Given Python 3.11+ with no third-party packages, when `scripts/retro_report.py --help` runs, then it exits 0 and prints usage covering `--root`, `--json`, and `--ccusage`.
- **AC2**: Given no `--root`, when it runs, then it scans `./specs/*/state.json`; given `--root` repeated, it scans every root and reports each run once with its root identified.
- **AC3**: Given runs under several roots, when reported, then it lists every run and aggregates by size, by mode, by domain (`domains`, a run may have several and counts under each), and by final stage (done / in progress / blocked).
- **AC4**: Given a run with `metrics.gates.*` and `stage_started_at`, when reported, then it shows total duration split into gate wait (sum of `approved_at - presented_at`) and agent time (total minus wait), plus time per stage with gate waits excluded.
- **AC5**: Given a complete run, when reported, then it shows gate rework per gate, review first-pass rate (`first_pass/total`), retries, interventions, and wave stats (task-minutes against wall-minutes) when `metrics.waves` exists.
- **AC6**: Given an old-format run missing a field (e.g. no `metrics.gates`, no `waves`, no `domains`), when reported, then that value shows as unknown and is excluded from averages and totals, never counted as 0.
- **AC7**: Given a `state.json` that is unreadable, invalid JSON, or not an object, when the report runs, then that run is listed as skipped with the reason, the others still report, and the exit code is 0.
- **AC8**: Given an in-progress or blocked run, when reported, then it appears with its stage and `blocked` reason, and its not-yet-reached values are unknown.
- **AC9**: Given runs where `blocked` is set, when aggregated, then the report gives the number of blocked stops overall and per size, domain, and mode, with each reason visible.
- **AC10**: Given no `--json`, when run, then stdout is a Markdown table of runs and of the aggregates; unknown shows as `unknown`, unavailable cost as `n/a`.
- **AC11**: Given `--json`, when run, then stdout is a single JSON document with `schema_version`, per-run records (`null` for unknown), skipped runs with reasons, and aggregates; the schema is documented in `docs/efficiency.md`.
- **AC12**: Given no `--ccusage`, when reported, then tokens are unknown (`null` in JSON) and ccusage is never invoked.
- **AC13**: Given `--ccusage` and ccusage missing or failing, when run, then the report completes (exit 0) with tokens unknown, cost `n/a`, and a note that cost is unavailable.
- **AC14**: Given `--ccusage` and ccusage output (faked in tests), when run, then token and cost data are merged into the table and JSON.
- **AC15**: Given fixture runs (complete, old-format, in-progress, blocked, malformed) in `tests/`, when `python3 -m unittest discover -s tests` runs, then the new tests pass without network or ccusage.
- **AC16**: Given `docs/efficiency.md`, when read, then it explains how to run the script, what each number means (including tokens only via `--ccusage`), and the JSON schema; and the roadmap item is moved to Done.

## Constraints
- Stdlib only, Python 3.11+, offline; read-only on run folders.
- Output must not embed absolute home paths beyond what the user passed as `--root`.
- Existing runs show inconsistent timestamps (see question 2), so no crash on negative or out-of-order values.

## Requirement changes

### Area: metrics-report
Purpose: Aggregate spec-agent run metrics across projects.
#### ADDED: Run discovery and tolerance
The system SHALL find runs under one or more roots, report each, treat missing fields as unknown (never zero), and skip malformed runs with a reason without failing the rest. (AC2, AC6, AC7, AC8)
#### ADDED: Per-run and grouped aggregate metrics
The system SHALL report duration (agent time, gate wait, per stage), gate rework, review first-pass rate, retries, interventions, wave stats, and criteria passed, aggregated by size, domain, and mode, plus blocked-stop counts. (AC3, AC4, AC5, AC9)
#### ADDED: Markdown and JSON output
The system SHALL print a Markdown table by default and a documented, versioned JSON document with `--json`. (AC10, AC11)
#### ADDED: Optional ccusage tokens and cost
The system SHALL report tokens and cost only from ccusage when `--ccusage` is given and works, else tokens unknown and cost `n/a`. (AC12, AC13, AC14)

## Open questions
1. "Criteria passed" has no field in `state.json` (tasks list criteria, not results). Is `retro.md`'s `Criteria passed` row the only source, and may the script parse that markdown row? *Matters: the retro format becomes a parsed contract; unknown when absent.*
2. `specs/012-aicfg-doctor/state.json` has `approved_at` earlier than `presented_at` (plan gate) and out-of-order `stage_started_at`. Flag as invalid and exclude, or clamp? *Matters: negative waits would skew totals.*
3. How does ccusage data map to a run (date range from `started_at` to done, or project/session)? Which ccusage command and output format is assumed? *Matters: attribution is the only way tokens/cost can be per-run, and the format can't be verified here.*
4. Duration for in-progress runs: use now, last stage start, or unknown? *Matters: affects averages.*
5. Should size, mode, and rework averages include skipped/in-progress runs? *Matters: aggregate denominators.*
6. A multi-domain run counts under each domain, so domain rows sum to more than the run count; is that acceptable, or should it split or use a primary domain? Runs with no `domains`: an "unknown" group? *Matters: domain averages double-count otherwise.*
7. Is a blocked stop only a run whose `blocked` is set now, or also runs that were blocked and later resumed (if the engine clears the field, history is lost)? *Matters: the count may undercount without a new field, which is out of scope.*
