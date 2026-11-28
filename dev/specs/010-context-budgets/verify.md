# Verify: Always-loaded token budgets; trim unslop

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_always_tokens_counts_rules_and_descriptions`, `test_core_over_budget_fails_naming_the_biggest_items` (also through `cmd_validate`); real run: `validate --pack` on a copy with `max_always_tokens = 10` → `ERROR acme: ~151 always-loaded tokens, budget 10 (biggest: …)` | pass |
| AC2 | `CORE_ALWAYS_BUDGET = 3000`; `test_pack_over_its_declared_budget_fails`, `test_pack_without_a_budget_warns_above_the_default` | pass |
| AC3 | `test_long_description_warns` | pass |
| AC4 | `test_tokens_shows_budget_per_source`; real `tokens` ends `core: ~2577 / 3000 always-loaded tokens` | pass |
| AC5 | `UnslopSplitTest`: all 93 rule lines from the old body present under `skills/unslop/`; SKILL.md 5.9k chars (was 13.8k), links all three references; description 60 tokens (was 116) | pass |
| AC6 | doc-types description 96 tokens (was 102); `validate` prints no WARN for core | pass |
| AC7 | `docs/packs.md` Context cost + `pack.toml` example; `docs/efficiency.md` two rows; example pack declares `max_always_tokens = 400`; VERSION 0.3.11, CHANGELOG tagged **[pack contract]** | pass |
| AC8 | `BudgetTest` (7 tests), red first on a stub | pass |

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK, no warnings; `validate --pack examples/pack-acme` → OK

## Numbers
Core always-loaded: ~2,639 → ~2,577 tokens (budget 3,000). `unslop` on use: SKILL.md 3,459 → 1,488
tokens, references 2,062 load only when a pass needs them.

## Changes from the plan
- The preservation test is a guard, so it passed before the move; the red for T2 was the
  SKILL.md size and description test (13,833 chars, failing) instead.
- The example pack now declares a budget, so it demonstrates the key.
