# Plan: Metrics rollup across spec-agent runs

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none (stdlib only; ccusage stays optional and is never installed)
- **Public API / contract changes:** new script `scripts/retro_report.py` and its versioned JSON output (`schema_version: 1`), documented in `docs/efficiency.md`
- **Migrations / data changes:** none (read-only on run folders)
- **Security triggers touched:** none (one subprocess, `ccusage`, run as an argument list with a timeout, only under `--ccusage`)
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Split parsing from rendering. `scripts/retro_metrics.py` turns one run folder into a `RunRecord` dataclass (every metric `None` when unknown) or a `Skipped(path, reason)`. Durations come from `metrics.started_at`, `stage_started_at`, and `metrics.gates.*` per `skills/spec-agent/references/state.md`: total = `stage_started_at.done - started_at`, gate wait = sum of `approved_at - presented_at`, agent = total - wait, per-stage = next stage start - this start minus the gate wait inside it. Any negative gap or out-of-order stage adds a warning and sets the affected values to `None` (no clamping); `specs/012-aicfg-doctor` is the real-world case. Non-`done` runs get `None` durations. Criteria passed mirrors `_criteria` in `scripts/evals.py` (Result column found by header name only, no last-column fallback, so a strict copy rather than an import of a private name), then the `Criteria passed` row of `retro.md`. Past blocks come from `log.md` headers matching `^## <agent> · <task> · blocked$` (`references/handoff.md`), reason from that block's `**Open issues:**` or `**Did:**` line.

`scripts/retro_aggregate.py` groups records by size, mode, domain (multi-domain counts in each, `none` for missing/empty; output notes rows can sum past the run count), and final stage (done / in progress / blocked). Counts use every record; each average carries its `n` and uses known values only; duration averages use done runs only (AC19). Blocked stops = current `blocked` + past log blocks, with reasons listed per group.

`scripts/retro_ccusage.py` runs `ccusage daily --json --since YYYYMMDD --until YYYYMMDD` (found via `shutil.which`, 30 s timeout), sums `totalTokens`/`totalCost` over days in range, and returns `None` on any failure. Tests put a stub `ccusage` script on `PATH`. `scripts/retro_report.py` is the argparse CLI: `--root` (repeatable, default `.`; scans `<root>/specs/*/state.json`, dedupes by resolved path, labels runs with the root string as passed so no other absolute paths leak), `--json`, `--ccusage`; renders Markdown or JSON; always exits 0 unless arguments are invalid. Sibling modules are imported by inserting the script's own directory on `sys.path`.

## Files
| File | Change |
|---|---|
| `scripts/retro_metrics.py` | new: load one run, per-run metrics, warnings, criteria, log blocks |
| `scripts/retro_aggregate.py` | new: grouping, counts, averages with n, blocked stops |
| `scripts/retro_ccusage.py` | new: optional ccusage period totals |
| `scripts/retro_report.py` | new: CLI, discovery, Markdown and JSON rendering |
| `tests/test_retro_{metrics,aggregate,ccusage,report}.py` | new: fixtures built in temp dirs |
| `docs/efficiency.md`, `docs/roadmap.md`, `changelog.d/024-metrics-rollup.md` | modify / new |

## Risks
- Unknown silently becoming 0 in sums, mitigated by `None` throughout and tests asserting old-format runs leave totals and `n` unchanged.
- ccusage output shape drift, mitigated by tolerant parsing (missing keys → unavailable) and a stub-based test for each failure mode.

## Test strategy
Unit tests per module with `unittest`, run folders written to `tempfile` dirs (complete, old-format, in-progress, blocked with `log.md`, malformed, bad timestamps). `test_retro_report.py` runs the CLI via `subprocess` with `PATH` set to a stub dir (or empty of ccusage) to cover AC1, AC2, AC10–AC15 end to end. No network.

## Tasks
- [ ] **T1** [agent: implementer] `RunRecord`/`Skipped` and per-run metrics: load and skip, durations, per-stage time, rework, first-pass, retries, interventions, waves, unknowns, timestamp warnings; `criteria_passed` and `blocked_stops` fields defined (filled in T2)
  - files: `scripts/retro_metrics.py`, `tests/test_retro_metrics.py`
  - criteria: AC4, AC5, AC6, AC7, AC8, AC18
- [ ] **T2** [agent: implementer] Criteria passed from `verify.md` / `retro.md`, past blocked stops from `log.md` headers
  - files: `scripts/retro_metrics.py`, `tests/test_retro_metrics.py`
  - criteria: AC9, AC17
  - after: T1
- [ ] **T3** [agent: implementer] Aggregates by size, mode, domain, final stage; averages with n; done-only durations; blocked-stop counts and reasons
  - files: `scripts/retro_aggregate.py`, `tests/test_retro_aggregate.py`
  - criteria: AC3, AC9, AC19
  - after: T1
- [ ] **T4** [agent: implementer] ccusage period totals with stub-on-PATH tests (missing, non-zero exit, bad JSON, success)
  - files: `scripts/retro_ccusage.py`, `tests/test_retro_ccusage.py`
  - criteria: AC13, AC14
- [ ] **T5** [agent: implementer] CLI: `--help`, root discovery and dedupe, Markdown and JSON (`schema_version`, runs, skipped, aggregates, period usage), `--ccusage` wiring and never-invoked default
  - files: `scripts/retro_report.py`, `tests/test_retro_report.py`
  - criteria: AC1, AC2, AC10, AC11, AC12, AC13, AC14, AC15
  - after: T2, T3, T4
- [ ] **T6** [agent: implementer] Docs: how to run, meaning of each number, JSON schema, tokens only via `--ccusage`; roadmap item to Done; changelog fragment (`bump: patch`)
  - files: `docs/efficiency.md`, `docs/roadmap.md`, `changelog.d/024-metrics-rollup.md`
  - criteria: AC11, AC16
  - review: batch
  - after: T5
