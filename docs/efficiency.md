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
| Plan summarized via `terraform show -json` + jq | `skills/terraform` | resource actions instead of full plan text |
| Checks scoped to changed packages/roots during implement | `references/efficiency.md` | faster loops; full run once at verify |
| Domain skills load on demand | Agent Skills progressive disclosure | only the stacks touched cost tokens |
| Short, de-duplicated global rules | `rules/` | rules load in every session of every tool |
| Static role files, variable text last | `agents/`, dispatch prompt | stable prefixes for prompt caching |

Measure with the metrics in each run's `retro.md`, plus token/cost tools below.

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
