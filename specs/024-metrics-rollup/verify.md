# Verify: Metrics rollup across spec-agent runs

Run at 2026-10-21T03:03:57Z on commit `e1d5e8a` (working tree clean). Raw output: `specs/024-metrics-rollup/.runs/`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 306 ran, 0 failed (`.runs/test.log`) |
| Targeted (new tests, verbose) | `python3 -m unittest discover -s tests -p 'test_retro_*.py' -v` | pass: 72 ran, 0 failed, all `ok` (`.runs/test-new-verbose.log`) |
| Lint | none configured | not configured |
| Build | none configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: `OK: 26 skills, 9 agents, 0 commands` (`.runs/validate.log`, exit 0) |
| Plan / diff | n/a | offline only |
| CLI: help | `python3 scripts/retro_report.py --help` | pass, exit 0 (`.runs/cli-help.log`) |
| CLI: Markdown | `python3 scripts/retro_report.py --root specs` | pass, exit 0, 35 runs (`.runs/cli-md.log`) |
| CLI: JSON | `python3 scripts/retro_report.py --root specs --json` | pass, exit 0, `schema_version` 1 (`.runs/cli-json.parsed.json`, `.runs/cli-json.summary.txt`) |
| CLI: multi-root | `--root specs --root <scratch>/root2` (one fixture run) | pass, exit 0, 36 runs, fixture listed under its own root (`.runs/cli-multiroot.log`, `.runs/cli-multiroot-json.summary.txt`) |
| CLI: skipped | `--root <scratch>/root3` (invalid JSON + non-object) | pass, exit 0, both listed with reasons (`.runs/cli-skipped-md.log`, `.runs/cli-multiroot-json.summary.txt`) |
| CLI: ccusage absent | `--root specs --ccusage` | pass, exit 0, `Tokens: unknown. Cost: n/a.` plus note (`.runs/ccusage-which.log` shows `command -v ccusage` exit 1; `.runs/cli-ccusage.log`, `.runs/cli-ccusage-json.log`) |

Scratch roots are under the session scratchpad (`/tmp/claude-0/-home-user-ai-config/bb6b11af-d4d6-51ac-beaf-b202f60c9428/scratchpad/root2`, `.../root3`), not in the repo.

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_retro_report.ReportTest.test_help_lists_flags`; manual `--help`: exit 0, lists `--root DIR`, `--json`, `--ccusage` (`.runs/cli-help.log`) | pass |
| AC2 | `test_default_root_is_cwd_specs`, `test_multiple_roots_and_dedupe`, `test_root_may_be_specs_dir_itself`; manual multi-root: 36 runs, fixture row carries its root path (`.runs/cli-multiroot.log:44`) | pass |
| AC3 | `test_retro_aggregate.AggregateTest.test_counts_by_size_mode_and_stage`, `test_multi_domain_counts_under_each_and_none_group`; manual `.runs/cli-md.log` "By domain" has `none` row (26 runs) and the note "domain rows can sum past the run count" (`cli-md.log:78`) | pass |
| AC4 | `test_retro_metrics.RetroMetricsTest.test_complete_run_durations`, `test_per_stage_excludes_gate_wait`; manual `specs/006-evals`: total 15.2 = agent 5.0 + gate wait 10.2 (`.runs/cli-md.log`) | pass |
| AC5 | `test_rework_first_pass_retries_interventions`, `test_wave_stats`; manual `specs/024-metrics-rollup` row shows wave ratio 1.7 (= 6.3 / 3.7 from state.json) (`cli-md.log:23`) | pass |
| AC6 | `test_old_format_unknowns_are_none`, `test_no_metrics_at_all`, `test_zero_values_stay_zero`; manual: old runs show `unknown`, averages exclude them (`cli-md.log` rows 010-018) | pass |
| AC7 | `test_skipped_cases`, `test_unreadable_missing_and_non_utf8`, `test_wrong_types_are_unknown`; manual skipped check: invalid JSON and list root both listed, exit 0 | pass |
| AC8 | `test_in_progress_run`, `test_blocked_run`; manual: `specs/024-metrics-rollup` (stage verify) shows total `unknown`, first-pass and other values known only where reached | pass |
| AC9 | `test_blocked_stops_from_log`, `test_blocked_stops_current_plus_past`, `test_blocked_stops_no_log_only_current`, `test_current_block_in_blocked_stops_counts_once`, `test_blocked_stop_entries_may_be_dicts_with_reason`; manual: "Blocked stops (0)" section present for specs | pass |
| AC10 | `test_markdown_default`; manual `.runs/cli-md.log` is Markdown, `unknown` and `n/a` used | pass |
| AC11 | `test_json_document_shape`; manual: `.runs/cli-json.parsed.json` parses as one document with `schema_version`, `runs`, `skipped`, `aggregates`, `usage`; schema documented at `docs/efficiency.md:53-63` | pass |
| AC12 | `test_no_ccusage_flag_never_invokes_it`; manual `--root specs --json`: `usage.requested` false, `tokens` null, note "run with --ccusage" | pass |
| AC13 | `test_ccusage_missing_degrades`, `test_ccusage_failing_degrades`, `test_non_zero_exit_is_unavailable`, `test_timeout_is_unavailable`; manual with ccusage not on PATH: exit 0, `Cost: n/a`, note "ccusage cost unavailable" (`.runs/cli-ccusage.log`, `.runs/cli-ccusage-json.log`) | pass |
| AC14 | Stub tests only: `test_ccusage_period_total`, `test_success_uses_totals_and_range_flags`, `test_success_sums_daily_when_no_totals`. ccusage is not installed, so no real-tool check was possible. The period-total label is in the output. The flags and JSON shape are untested against a real install (`docs/efficiency.md:51` says so). | pass (stub-verified only) |
| AC15 | `python3 -m unittest discover -s tests`: 306 ran, OK (`.runs/test.log`); 72 new `test_retro_*` tests all `ok` (`.runs/test-new-verbose.log`). Runs offline, no ccusage. | pass |
| AC16 | `docs/efficiency.md:24-51` (run command line 29, how to run; what each number means table 31-46; tokens only via `--ccusage` lines 48-51); JSON schema `docs/efficiency.md:53-63`; roadmap item moved to Done at `docs/roadmap.md:12` (under `Done:` at line 11) | pass |
| AC17 | `test_criteria_from_verify_table`, `test_criteria_result_column_found_by_header`, `test_criteria_verify_wins_over_retro`, `test_criteria_retro_fallback`, `test_criteria_unknown`, `test_criteria_without_result_header_is_unknown`; manual: `specs/005-core-version-contract` shows `10/10` | pass |
| AC18 | `test_negative_total`, `test_out_of_order_stages`, `test_approved_before_presented`, `test_wait_exceeding_total_flags_negative_agent_time`, `test_unparseable_timestamp`; manual on `specs/012-aicfg-doctor` (`.runs/cli-md.log`): warnings name the out-of-order stage and approved-before-presented, durations shown as unknown, no clamping | pass |
| AC19 | `test_averages_use_known_values_only_with_n`, `test_duration_averages_use_done_runs_only`, `test_non_duration_averages_include_unfinished_runs`, `test_unknown_everywhere_gives_none_avg_and_zero_n`; manual: `Aggregates (35 runs)` matches the 35 parsed runs; averages carry `(n=…)`; skipped runs absent from aggregates | pass |

## Notes
- No flaky tests; no reruns were needed.
- `.runs/cli-json.log`, `cli-multiroot-json.log`, and `cli-ccusage-json.log` end with an `exit=` line appended by the shell. The `*.parsed.json` copies are the document alone.
- AC14 is verified by stub tests only (ccusage not installed). This is the one criterion without a real-tool check.
- Skipped-run paths and multi-root labels show the absolute scratch paths because those were passed as `--root`. Repo-root runs print relative paths.
- The spec run's own row shows `verify` stage and unknown criteria because `verify.md` did not exist yet during the run.
