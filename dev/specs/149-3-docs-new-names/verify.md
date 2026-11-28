# Verify: Move docs and references to the new skill names

Spec: [spec.md](spec.md) · Commit: 8eed51b

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 771 ran, OK (1 skipped), on the committed tree |
| Validate | `python3 scripts/brainrc.py validate` | pass: OK, 32 skills, 10 agents (links and token budgets) |
| Tutorial | `python3 scripts/check_tutorial.py` | pass: steps 1-5 |
| README quickstart | `python3 scripts/check_tutorial.py --readme` | pass |
| Secret scan | gitleaks 8.24.3 over `149-2-reserved-names..HEAD` | pass: no leaks |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | in-scope `rg` leftovers: 9, all legitimate (plan.md paths, status values, the deprecation note); review found no over- or under-replacement | pass |
| AC2 | Domains table links `../brainrc-aws/SKILL.md`, `../brainrc-terraform/SKILL.md`; validate checks links | pass |
| AC3 | docs/harness-packages.md deprecation note (aliases until 0.6.0; Antigravity may ignore `disable-model-invocation`) | pass |
| AC4 | README 100 lines; `--readme` pass | pass |
| AC5 | changelog.d/149-3-docs-new-names.md lists renames, window, 0.6.0 | pass |
| AC6 | checks above | pass |
| AC7 | evals/triggers.toml 7 cases renamed, none dropped; test_planning, test_plugin_docs re-pinned; tests.test_evals OK | pass |

## Notes
- Eval case header comments and proof_guard.py's docstring still mention `/work`/`/plan` (out of scope; aliases still work).
