# Verify: Behavioural evals for spec-agent runs and skill triggers

Run at 2026-10-06T02:56:06Z on commit `a15a3c6`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 76 tests (59 before) |
| Validate | `python3 scripts/aicfg.py validate` (+ example pack) | pass |
| Tutorial | `specs/013-tutorial/run-tutorial.sh` | pass |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `CheckTest`: 9 checks pass on a good fake run; each kind fails on its broken variant; unknown ticket is a clean ERROR | pass |
| AC2 | `evals/cases/sandbox-001.toml` (11 checks); kinds validated by `CaseFileTest`; no-run sandbox → ERROR, exit 1 | pass (real run in #18) |
| AC3 | `evals/cases/sandbox-002.toml` (10 checks): planted text under Open questions, Spec gate approved, main untouched, --greeting, no .env committed | pass (real run in #18) |
| AC4 | `evals/triggers.toml` 15 cases; coverage test: every Domains skill has positive and negative; `TriggerTest` with a fake model; hand-made answer scores 15/15 | pass |
| AC5 | `check` takes any case path; `triggers` merges enabled packs' `evals/triggers.toml` | pass |
| AC6 | 17 offline tests in `tests/test_evals.py`, in default CI | pass |
| AC7 | `docs/evals.md`; README link; VERSION 0.3.5; CHANGELOG | pass |

## Notes
- No real model was run (spec decision). The sandbox cases get their first real runs in #18.
