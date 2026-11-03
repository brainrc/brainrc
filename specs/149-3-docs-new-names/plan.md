# Plan: Move docs and references to the new skill names

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none (docs follow the names 149.1 shipped)
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** none (docs)
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Find every use with `rg` over the in-scope paths (spec AC1), replace by hand (not a blind sed:
`plan` and `review` are common words; only skill and slash-command uses change). Repoint the
Domains table links. Add the deprecation note. `skills/spec-agent/scripts/proof_guard.py` is
code: leave it, and note any old-name string it holds.

## Files
| File | Change |
|---|---|
| README.md, CONTRIBUTING.md, docs/*.md, rules/*.md, agents/*.md, skills/**/*.md (not the five alias stubs), examples/sandbox/README.md | modify: old → new names |
| changelog.d/149-3-docs-new-names.md | new, patch |

## Risks
- Over-replacing ordinary words. Mitigation: review the diff for every `plan`/`review` change.
- Rule token budget: `/brainrc-work` is longer than `/work`. `validate` checks the budget.

## Test strategy
`validate` (links, budgets), the suite (tests that pin README text), both `check_tutorial.py`
modes, and an `rg` for leftovers in scope.

## Tasks
- [ ] **T1** [agent: implementer] Rename references in shipped docs, add the deprecation note, fragment
  - files: README.md, CONTRIBUTING.md, docs/, rules/, agents/, skills/ (excluding skills/{work,review,plan,aws,terraform}/), examples/sandbox/README.md, changelog.d/149-3-docs-new-names.md
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6
