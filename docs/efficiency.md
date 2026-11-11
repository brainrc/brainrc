# Efficiency: speed and tokens

## Built into this repo

| Technique | Where | Why it saves |
|---|---|---|
| Size-based execution mode | `spec-agent/references/efficiency.md` | trivial/small tickets run inline: no subagent spawn overhead |
| Implementer writes its own tests by default | `agents/implementer.md` | one agent run per task instead of two |
| Batched review, parallel reviewers | `spec-agent/SKILL.md` | one review pass per branch; concurrent read-only reviewers |
| Per-agent model tiers | `model:` in `agents/*.md` | routine roles (verify, docs) on the cheapest tier; budgets stop a cheap model from using more tokens than it saves (the k9s trial verifier: 45k tokens, 18 tool calls before its budget was added) |
| Paths, not contents, in dispatch | `references/handoff.md` | subagents load only what they need |
| Handoff blocks ≤ ~150 words; engine reads only the newest | `references/handoff.md` | main thread stays small across long runs |
| Command output to `.runs/`, read summaries | `references/efficiency.md` | test/plan logs never flood context |
| Plan summarized via `terraform show -json` + jq | `skills/brainrc-terraform` | resource actions instead of full plan text |
| Checks scoped to changed packages/roots during implement | `references/efficiency.md` | faster loops; full run once at verify |
| Domain skills load on demand | Agent Skills progressive disclosure | only the stacks touched cost tokens |
| Short, de-duplicated global rules | `rules/` | rules load in every session of every tool |
| Always-loaded token budgets | `validate` (`CORE_ALWAYS_BUDGET`, pack `max_always_tokens`) | rules and descriptions can't grow unnoticed; `tokens` shows each source against its budget ([packs](packs.md#context-cost)) |
| Long skills keep catalogues in `references/` | e.g. `skills/unslop` | the body read on every use stays short |
| Static role files, variable text last | `agents/`, dispatch prompt | stable prefixes for prompt caching |

Measure with the metrics in each run's `retro.md`, plus token/cost tools below.

## Metrics rollup

`scripts/retro_report.py` rolls up `specs/*/state.json` across runs. It is offline and read-only.

```
python3 scripts/retro_report.py [--root DIR]... [--json] [--ccusage]
```

`--root` (repeatable, default `.`) is a project root holding `specs/*/state.json`, or a specs dir.
Output is a Markdown table per run plus averages overall and by size, mode, domain, and final stage.
Minutes throughout. `unknown` means not recorded and is never counted as 0; averages show `n`, the runs where the value is known.

| Number | Meaning |
|---|---|
| Total min | start of run to done; unknown for in-progress or blocked runs. For a watched run it includes waiting for the PR to merge |
| Gate wait min | time parked at approval gates, waiting on a human; unknown if it exceeds total (inconsistent timestamps), with a warning, so it stays out of averages |
| Agent min | total minus gate wait: time the agent worked |
| First-pass | share of review passes that found nothing to fix; the aggregate is the average of per-run rates (with `n`) |
| Retries | each time a task goes back to the implementer |
| Interventions | each time the user has to step in outside a gate (answering a blocked stop, correcting the agent mid-stage) |
| Wave ratio | summed task minutes over wall minutes of parallel waves (above 1 means parallelism paid off) |
| Blocked stops | a run's current `blocked` reason plus each past `blocked` handoff in its `log.md`; counted once per stop, with the reasons listed per group |
| Criteria | passed/total acceptance criteria |
| Outcome | `merged`, `abandoned` (PR closed unmerged), or `unknown` (still open or not watched) |
| Post-merge | result of the post-merge verify: `pass`, `regression`, `unverified`, or `unknown` |
| Time to merge | PR opened to merged, in minutes, from timestamps; `unknown` if either is missing |
| Review rounds | review rounds handled by `watch` (`watch.review_rounds`) |
| CI failures | red checks recorded in `watch.ci_failures`, own and external |
| Warnings | inconsistent state, e.g. stages out of order; the run still counts |

Aggregates add **Avg time to merge** (with `n`), **Merged** and **Abandoned** run counts, and **Regressions** (runs whose post-merge verify found one). Runs without the `watch` fields show `unknown` in every new column, never 0.

Tokens and cost are not in `state.json`. They come only from `--ccusage`, which runs
`ccusage daily --json` for the date range of the reported runs, widened by one day on each side (ccusage buckets by local day, run stamps are UTC), and gives one **period total**, not a
per-run figure. Without the flag, or if ccusage is missing, fails, or the runs have no dates, tokens and cost stay `null`. The ccusage
flags and JSON shape are assumed from its docs and untested against a real install.

### JSON schema (`--json`, `schema_version` 2)

One document on stdout. Unknown values are `null`.

| Field | Content |
|---|---|
| `schema_version` | `2`; bumped on breaking changes |
| `runs[]` | one record per run: `path`, `slug`, `size`, `mode`, `domains`, `stage`, `blocked_reason`, `total_minutes`, `wait_minutes`, `agent_minutes`, `stage_minutes` (per stage), `gate_rework` (per gate), `first_pass_rate` (0-1), `retries`, `interventions`, `waves`, `wave_ratio`, `criteria_passed`, `outcome`, `post_merge`, `time_to_merge`, `review_rounds`, `ci_failures`, `blocked_stops`, `warnings` (new fields in version 2; `null` when unknown) |
| `skipped[]` | runs that could not be read: `path`, `reason` |
| `aggregates` | `runs`, `overall`, `by_size`, `by_mode`, `by_domain`, `by_stage`, `domain_note`, `blocked_stops`; each group has `runs`, `averages` (`{avg, n}` per field), `stage_minutes` and `gate_rework` (`{avg, n}` per key), `blocked_stops` (`count`, `reasons`), and the counts `merged`, `abandoned`, `regressions` (runs by `outcome` / `post_merge`; `averages.time_to_merge` is the mean) |
| `usage` | `requested`, `available`, `since`, `until`, `tokens`, `cost`, `note` |

## Optional external tools (researched 2026-09)

None are required. Evaluate against your own `retro.md` numbers before adopting. Savings
figures are as reported by the linked sources, not measured here.

| Tool | What it does | Reported effect | Notes |
|---|---|---|---|
| [ryoppippi/ccusage](https://github.com/ryoppippi/ccusage) | Token/cost reports from local Claude Code logs | measurement | Start here: measure before optimizing |
| [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | CLI proxy that compresses noisy command output | 60–90% on log-heavy output | Overlaps our `.runs/` discipline; helps in ad-hoc sessions |
| [oraios/serena](https://github.com/oraios/serena) | LSP-backed symbol-level code navigation/editing (MCP) | fewer full-file reads | Strong fit for large Go codebases |
| [Mibayy/token-savior](https://github.com/Mibayy/token-savior) | Symbol-level navigation MCP | ~43% in one comparison | Best on typed languages |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Terse-output skill/hooks | ~38% on prose output | Little effect on tool-heavy runs |
| [musistudio/claude-code-router](https://github.com/musistudio/claude-code-router) | Routes requests to cheaper models/providers | cost, not tokens | Our `model:` tiers cover the Claude-only case |
| [mksglu/context-mode](https://github.com/mksglu/context-mode) | Offloads large tool outputs to a searchable store | 20–98% on big outputs | Elastic License v2 (not OSI) |
| [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | Lightweight SDD with delta specs | ~250 vs ~800 lines per change vs spec-kit | Idea source; see roadmap for delta/living specs |

Skip tools under non-commercial licenses if you use this at work (e.g. PolyForm Noncommercial).

Sources: [computingforgeeks tool comparison](https://computingforgeeks.com/reduce-claude-code-token-usage-tools/),
[OpenSpec concepts](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md),
[OpenSpec vs Spec Kit](https://hashrocket.com/blog/posts/openspec-vs-spec-kit-choosing-the-right-ai-driven-development-workflow-for-your-team),
[ccusage](https://github.com/ryoppippi/ccusage).
