## Summary
Always-loaded token budgets, and a shorter `unslop`. Closes #10.

Rules and every skill, agent and command description load into every session, on every harness. Until now nothing stopped that growing.

- **`validate`:** it measures each source's always-loaded tokens (its rules plus its descriptions, using the same estimate as `tokens`).
  - Core's budget is `CORE_ALWAYS_BUDGET = 3000`. A pack sets its own with `max_always_tokens` in `pack.toml`.
  - Over budget is a FAIL that names the total, the budget, and the 3 biggest items.
  - A pack without a budget gets a WARN above 1,000 tokens.
  - Any description over 100 tokens gets a WARN.
- **`tokens`:** it now ends with each source's total against its budget, for example `core: ~2577 / 3000 always-loaded tokens`.
- **`unslop`:** sections A–I move word for word into `references/structure.md`, `clarity.md` and `change-prose.md`. SKILL.md drops from about 3.5k to about 1.5k tokens, and its description from 116 to 60. A fixture of all 93 rule lines checks that none was lost.
- **`doc-types`:** its description is trimmed under 100 tokens, so core raises no warnings.
- **Docs:** `docs/packs.md` and `docs/efficiency.md` cover the budgets. The example pack declares `max_always_tokens = 400`.

**[pack contract]**, non-breaking: the new key is optional, and packs without it only get a warning. So this is a PATCH bump to 0.3.11.

## Acceptance criteria
- [x] AC1 per-source measurement; over budget fails and names the biggest items
- [x] AC2 core 3,000; optional pack `max_always_tokens`; WARN above 1,000 without it
- [x] AC3 long-description WARN
- [x] AC4 `tokens` shows each source against its budget
- [x] AC5 `unslop` split with no rule lost; description 60 tokens or fewer
- [x] AC6 `doc-types` description under 100
- [x] AC7 docs, VERSION 0.3.11, CHANGELOG
- [x] AC8 tests

## Testing
- `python3 -m unittest discover -s tests -q` → OK. 9 new tests; the behaviour tests failed on assertions first.
- `python3 scripts/aicfg.py validate` (no warnings) and `validate --pack examples/pack-acme` → OK.
- Real run: `validate --pack` on a copy of the example pack with `max_always_tokens = 10` prints the FAIL with the 3 biggest items.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
