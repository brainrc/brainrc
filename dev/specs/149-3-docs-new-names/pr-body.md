Use the brainrc-* skill names in docs, rules, agents and evals

6 of 6 in epic #113, stacked on #<PREV_PR>. Retarget to `main` before merging. Part 3 of 3 of #149.

## Why
Parts 1 and 2 shipped the `brainrc-*` names and kept the old ones as aliases. The docs still taught the old names, which go away in 0.6.0.

## What changed
- README, CONTRIBUTING, docs/, rules/10-git.md, agents/, skills/ and the sandbox README use `/brainrc-work`, `/brainrc-review`, `/brainrc-plan`, `brainrc-aws` and `brainrc-terraform`. Ordinary words ("plan", "review", the `review` status) are unchanged.
- The spec-agent Domains table links `../brainrc-aws/SKILL.md` and `../brainrc-terraform/SKILL.md`.
- `docs/harness-packages.md`: the old names are deprecated aliases until 0.6.0, and Antigravity may still list them because it may ignore `disable-model-invocation`.
- `evals/triggers.toml`: cases expect or forbid `brainrc-aws` and `brainrc-terraform`, since the aliases no longer auto-trigger. No case dropped.
- Two tests re-pin shipped text to the new names (`/brainrc-plan`, `/brainrc:brainrc-work`). No assertion dropped.
- `specs/living/core-skill-names.md`: the new area from the parent spec.
- `changelog.d/149-3-docs-new-names.md` (patch): the renames, the alias window and the reserved-name check.

## Acceptance criteria
- [x] AC1-AC3: names, links and deprecation note (review, `rg`, validate)
- [x] AC4: README 100 lines, `check_tutorial.py --readme` passes
- [x] AC5: changelog fragment complete for #149
- [x] AC6: validate, 771 tests OK, both tutorial checks pass
- [x] AC7: evals and pinned tests follow the new names

## How to verify
```
python3 scripts/brainrc.py validate
python3 -m unittest discover -s tests
python3 scripts/check_tutorial.py --readme
```

## Decisions made without you
- The engine wrote this child's spec and plan from the parent spec (item 3 of its split). Gates auto-approved.
- Spec reworked once: the trigger evals and two pinned tests had to follow the new names (AC7). The first spec had excluded tests and evals.
- Eval case header comments, sandbox tickets, `specs/` records and `CHANGELOG.md` keep the old names; the aliases still work there.
- Ticket comment not posted.

## Follow-ups
- LOW: update the `/work` and `/plan` mentions in eval case header comments and in `proof_guard.py`'s docstring.
- 0.6.0: remove the five aliases and `DEPRECATED_ALIASES`.

Spec: `specs/149-3-docs-new-names/spec.md` · Parent: `specs/149-namespace-core-skills/spec.md`

Closes #149

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01Hn6pdU7RJ1sLQqc3fDP7Sa
