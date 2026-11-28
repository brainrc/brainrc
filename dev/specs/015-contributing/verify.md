# Verify: CONTRIBUTING.md for human contributors

Run at 2026-10-06T02:37:02Z on commit `5674cdc`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 59 tests |
| Validate | `python3 scripts/aicfg.py validate` | pass |
| CONTRIBUTING commands | fresh clone: `pip install pre-commit` (venv), `pre-commit install`, validate, unittest, `run-tutorial.sh` | all pass |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | sections: Setup, Making a change (branch, pack vs core, version bump, checks, PR with Closes #N), Using spec-agent, Where things are | pass |
| AC2 | rules stay in AGENTS.md; CONTRIBUTING links them; AGENTS.md links back. Overlap: two workflow steps (run the checks, bump VERSION) appear in both, as steps not content rules | pass, with that note |
| AC3 | README Adding content links CONTRIBUTING.md; VERSION 0.3.4; CHANGELOG entry; every command ran as written | pass |
