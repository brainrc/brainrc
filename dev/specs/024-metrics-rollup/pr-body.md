Add metrics rollup across spec-agent runs

## Why
`docs/efficiency.md` says to measure changes against the numbers in `retro.md`, but nothing reads those numbers across runs. Without a baseline, a change to a role or rule can't be shown to help. Older runs lack newer fields, so the rollup keeps "unknown" distinct from zero.

## What changed
- `scripts/retro_report.py` (stdlib, offline, read-only) rolls up `specs/*/state.json` over one or more `--root` dirs. Markdown by default; `--json` (`schema_version` 1) for tools.
- Per run: total, agent, and gate-wait minutes; time per stage; gate rework; first-pass rate; retries; interventions; wave ratio; criteria passed; warnings.
- Aggregates by size, mode, domain, and final stage. Each average shows its `n`. Blocked stops count the current block plus past `blocked` handoffs in `log.md`.
- Missing fields show `unknown` and stay out of averages. Malformed runs are listed as skipped with a reason. Out-of-order or negative timestamps raise a warning and drop the affected durations; nothing is clamped.
- `--ccusage` adds a period-total token and cost figure from `ccusage daily --json`. Off by default. If ccusage is missing or fails, tokens show `unknown` and cost `n/a`.
- Docs: usage, what each number means, and the JSON schema in `docs/efficiency.md`. Roadmap item moved to Done. Patch changelog fragment.

Sample aggregate rows from this repo's 35 runs (`--root specs`):

```
| Overall | Runs | Avg total | Avg agent | Avg gate wait | Avg first-pass | Avg retries | Avg interventions | Blocked stops |
|---|---|---|---|---|---|---|---|---|
| all | 35 | 178 (n=34) | 4.3 (n=22) | 218.5 (n=22) | 77% (n=16) | 0.1 (n=35) | 0.2 (n=35) | 0 |
| small | 9 | 82 (n=9) | 1.3 (n=8) | 88.8 (n=8) | 100% (n=2) | 0 (n=9) | 0.2 (n=9) | 0 |
```

This run's own row shows a wave ratio of 1.7 (6.3 task-min over 3.7 wall-min, two waves).

## Acceptance criteria
Checked against `specs/024-metrics-rollup/verify.md`.
- [x] AC1–AC2: `--help` lists the flags; no `--root` scans `./specs`; repeated `--root` reports each run once with its root (`tests/test_retro_report.py`).
- [x] AC3, AC19: counts and aggregates by size, mode, domain, and stage; averages use known values only (`tests/test_retro_aggregate.py`).
- [x] AC4–AC6, AC8: durations, gate wait, per-stage time, rework, first-pass, retries, interventions, waves; unknowns; in-progress and blocked runs (`tests/test_retro_metrics.py`).
- [x] AC7, AC18: skipped runs carry a reason; bad timestamps warn and are excluded (`tests/test_retro_metrics.py`, `tests/test_retro_report.py`).
- [x] AC9, AC17: blocked stops from `log.md`; criteria from `verify.md`, falling back to `retro.md` (`tests/test_retro_metrics.py`, `tests/test_retro_aggregate.py`).
- [x] AC10–AC13: Markdown and JSON output; ccusage never runs without `--ccusage`; ccusage failures degrade cleanly (`tests/test_retro_report.py`, `tests/test_retro_ccusage.py`).
- [x] AC14: period totals, checked with a stub `ccusage` only (see follow-ups).
- [x] AC15–AC16: 306 tests pass offline; docs and roadmap updated.

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/retro_report.py --root specs
python3 scripts/retro_report.py --root specs --json
python3 scripts/retro_report.py --root specs --ccusage   # without ccusage: "Tokens: unknown. Cost: n/a."
python3 scripts/aicfg.py validate
```

## Follow-ups
- ccusage flags and JSON shape are assumed from its docs, not tested against a real install. Run `--ccusage` once against a real install before trusting the cost column.
- Later fields will feed the rollup: the `watch` stage (#77), outcome measures (#75), understanding (#69), and session tokens (#73). None is in scope here, and `state.json` is unchanged.
- Review findings from F1 and F2 are fixed; none are open.

Closes #24. Also covers #76, which was closed as a duplicate of #24.

Spec: `specs/024-metrics-rollup/spec.md` · Plan: `specs/024-metrics-rollup/plan.md` · Verify: `specs/024-metrics-rollup/verify.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01BdiJDGmXUuJTx5qC4ADnaF
