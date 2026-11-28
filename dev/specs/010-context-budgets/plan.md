# Plan: Always-loaded token budgets; trim unslop

Inline mode, tests first per task. One review pass over the whole diff before Verify.

| Task | What | Files | Criteria | Red test |
|---|---|---|---|---|
| T1 | `always_tokens(src)` → (total, items) using the same estimate as `tokens`; `check_budgets(srcs)` → (errors, warnings) called from `validate`; `tokens` prints per-source total vs budget | `scripts/aicfg.py`, `tests/test_aicfg.py` | AC1–AC4, AC8 | `BudgetTest`: core over a lowered budget fails naming top 3; pack over declared `max_always_tokens` fails; pack over 1,000 undeclared warns; long description warns; current core passes clean |
| T2 | `unslop`: move sections A–E to `references/structure.md`, F–H to `references/clarity.md`, I to `references/change-prose.md` verbatim; Process steps link them; description ≤ 60 tokens. `doc-types` description < 100 tokens | `skills/unslop/**`, `skills/doc-types/SKILL.md`, `tests/test_aicfg.py` | AC5, AC6 | test: every non-blank line of the old SKILL.md body (from git, pinned as a fixture list of rule lines) exists in some file under `skills/unslop/`; description ≤ 60 tokens |
| T3 | Docs and release | `docs/efficiency.md`, `docs/packs.md`, `VERSION` 0.3.11, `CHANGELOG.md` | AC7 | `validate` |

## Shape of T2's preservation test
Snapshot the old body's rule lines (bullets and numbered items under sections A–I) into
`tests/fixtures/unslop-rules.txt` before moving anything; the test asserts each line appears
verbatim somewhere in `skills/unslop/`. Red: run it after creating the empty reference files
but before moving text.

## Risks
- Process steps refer to "section A" etc.: kept as headings in the reference files, so the
  letters still resolve; each step gets a link.
- `validate` already checks reference links resolve, so a broken link fails CI.
