# Spec: Metrics rollup across spec-agent runs

Ticket: gh:24 · Size: standard · Status: approved

## Problem
Each spec-agent run records metrics in `state.json` and `retro.md`, but nothing reads them across runs. `docs/efficiency.md` says to "measure against your retro.md numbers", yet there is no baseline, so the owner cannot tell whether a change to a role or rule helped. Older runs lack newer fields, so any rollup must distinguish "unknown" from zero.

## Goals
- One offline command reports per-run and aggregate metrics over runs under one or more roots, grouped by size, domain, and mode.
- Output is a Markdown table for people and a versioned JSON document for tools.
- Optional token and cost data from ccusage, with clean degradation when it is absent.

## Non-goals
- New fields in `state.json` (including a token field), or changes to what the engine records.
- The `watch` stage, outcome measures, or the session-token mod (#73).
- Writing to run folders, or fixing or clamping bad timestamps in old runs.
- Installing or requiring ccusage, or per-run token attribution.

## Acceptance criteria
- **AC1**: Given Python 3.11+ with no third-party packages, when `scripts/retro_report.py --help` runs, then it exits 0 and prints usage covering `--root`, `--json`, and `--ccusage`.
- **AC2**: Given no `--root`, when it runs, then it scans `./specs/*/state.json`; given `--root` repeated, it scans every root and reports each run once with its root identified.
- **AC3**: Given runs under several roots, when reported, then it lists every run and aggregates by size, by mode, by domain, and by final stage (done / in progress / blocked). A multi-domain run counts under each of its domains, and the report notes that domain rows can sum past the run count; runs with no `domains` go in a group named `none`.
- **AC4**: Given a run with `metrics.gates.*` and `stage_started_at`, when reported, then it shows total duration split into gate wait (sum of `approved_at - presented_at`) and agent time (total minus wait), plus time per stage with gate waits excluded.
- **AC5**: Given a complete run, when reported, then it shows gate rework per gate, review first-pass rate (`first_pass/total`), retries, interventions, and wave stats (task-minutes against wall-minutes) when `metrics.waves` exists.
- **AC6**: Given an old-format run missing a field (e.g. no `metrics.gates`, no `waves`, no `domains`), when reported, then that value shows as unknown and is excluded from averages and totals, never counted as 0.
- **AC7**: Given a `state.json` that is unreadable, invalid JSON, or not an object, when the report runs, then that run is listed as skipped with the reason, the others still report, and the exit code is 0.
- **AC8**: Given an in-progress or blocked run, when reported, then it appears with its stage and `blocked` reason, its duration is unknown, and its other not-yet-reached values are unknown.
- **AC9**: Given runs, when aggregated, then the report gives the number of blocked stops overall and per size, domain, and mode, with each reason visible. A blocked stop is a run with `blocked` set now, or a past block found as a handoff header in `log.md` whose status is `blocked` (format in `skills/spec-agent/references/handoff.md`). A run with no `log.md` contributes only its current block.
- **AC10**: Given no `--json`, when run, then stdout is a Markdown table of runs and of the aggregates; unknown shows as `unknown`, unavailable cost as `n/a`.
- **AC11**: Given `--json`, when run, then stdout is a single JSON document with `schema_version`, per-run records (`null` for unknown), skipped runs with reasons, and aggregates; the schema is documented in `docs/efficiency.md`.
- **AC12**: Given no `--ccusage`, when reported, then tokens are unknown (`null` in JSON) and ccusage is never invoked.
- **AC13**: Given `--ccusage` and ccusage missing or failing, when run, then the report completes (exit 0) with tokens unknown, cost `n/a`, and a note that cost is unavailable.
- **AC14**: Given `--ccusage` and `ccusage daily --json` output (faked in tests), when run, then total tokens and cost for the date range the reported runs cover are shown in the table and JSON, labeled as a period total, not per run.
- **AC15**: Given fixture runs (complete, old-format, in-progress, blocked, malformed) in `tests/`, when `python3 -m unittest discover -s tests` runs, then the new tests pass without network or ccusage.
- **AC16**: Given `docs/efficiency.md`, when read, then it explains how to run the script, what each number means (including tokens only via `--ccusage`), and the JSON schema; and the roadmap item is moved to Done.
- **AC17**: Given a run with `verify.md` containing an Acceptance criteria table, when reported, then criteria passed is read from that table's Result column, found by header name; if absent, from the `Criteria passed` row of `retro.md`; else unknown.
- **AC18**: Given a run with `approved_at` before `presented_at`, out-of-order stage timestamps, or a negative duration, when reported, then the run carries a warning naming the problem, the affected durations are excluded from totals and averages, and no value is clamped or adjusted.
- **AC19**: Given aggregates, when computed, then counts include every parsed run; each average uses only runs where its value is known and shows its n; duration averages use done runs only; skipped runs appear only in the skipped list.

## Constraints
- Stdlib only, Python 3.11+, offline; read-only on run folders.
- Output must not embed absolute home paths beyond what the user passed as `--root`.
- No crash on negative or out-of-order timestamps (e.g. `specs/012-aicfg-doctor/state.json`).

## Requirement changes

### Area: metrics-report
Purpose: Aggregate spec-agent run metrics across projects.
#### ADDED: Run discovery and tolerance
The system SHALL find runs under one or more roots, report each, treat missing fields as unknown (never zero), skip malformed runs with a reason without failing the rest, and flag invalid timestamps with a warning and exclude them from totals. (AC2, AC6, AC7, AC8, AC18)
#### ADDED: Per-run and grouped aggregate metrics
The system SHALL report duration (agent time, gate wait, per stage), gate rework, review first-pass rate, retries, interventions, wave stats, and criteria passed, aggregated by size, domain, and mode with stated denominators, plus blocked-stop counts including past blocks from `log.md`. (AC3, AC4, AC5, AC9, AC17, AC19)
#### ADDED: Markdown and JSON output
The system SHALL print a Markdown table by default and a documented, versioned JSON document with `--json`. (AC10, AC11)
#### ADDED: Optional ccusage tokens and cost
The system SHALL report period-total tokens and cost from `ccusage daily --json` only when `--ccusage` is given and works, else tokens unknown and cost `n/a`. (AC12, AC13, AC14)

## Open questions
None.
