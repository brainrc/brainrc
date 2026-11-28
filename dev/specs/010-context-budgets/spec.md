# Spec: Always-loaded token budgets; trim unslop

Ticket: gh:10 · Size: standard (aicfg.py, tests, unslop split, two docs; 3 design choices) · Status: draft

## Problem
Rules and every skill, agent, and command description load in every session, on every
harness. Today that's ~2,660 tokens for core (rules 655, descriptions 2,009) and nothing stops
it growing, from core or from a pack.

## Acceptance criteria
- **AC1** `validate` measures each source's always-loaded tokens (its rules plus its skill,
  agent, and command descriptions, with the same estimate as `tokens`) and fails when it is
  over budget, naming the total, the budget, and the 3 biggest items.
- **AC2** Budgets: core `CORE_ALWAYS_BUDGET = 3000` in `aicfg.py`; a pack sets
  `max_always_tokens` in `pack.toml`. A pack without it gets a WARN above 1,000 tokens, not a
  failure (see choice 1).
- **AC3** A description over 100 tokens is a WARN naming it.
- **AC4** `tokens` prints each source's always total against its budget.
- **AC5** `unslop`: description ≤ 60 tokens; SKILL.md keeps the process, register, and
  checklist, and moves the long rule catalogue sections into `references/` files that
  SKILL.md links, so no rule is dropped (see choice 3). Every rule line before the change is
  still present in `skills/unslop/` after it (test).
- **AC6** `doc-types` description trimmed under 100 tokens so core has no WARN.
- **AC7** `docs/efficiency.md` and `docs/packs.md` document the budgets and `max_always_tokens`;
  VERSION 0.3.11 with a CHANGELOG entry tagged **[pack contract]** (new optional key).
- **AC8** Tests: core under budget passes; core over budget fails naming items; pack over its
  declared budget fails; pack over 1,000 without a budget warns; long description warns.

## Design choices
1. **Packs without `max_always_tokens` get a WARN, not a FAIL.** A default FAIL would break
   existing packs and force a MINOR bump (pins are `<0.4`). The key is new and optional, so
   this is PATCH; packs opt into enforcement by declaring a budget.
2. **Core budget 3,000** (~340 above today, ~400 after this ticket's trims): room for a few
   more skills, small enough that a new rule or long description shows up in review.
3. **Unslop is split, not rewritten.** Moving rule sections verbatim into `references/` (loaded
   on use, like spec-agent's) cuts the always-read SKILL.md without editorial risk to the rules.
   A test checks no rule line was lost.

## Open questions
None.
