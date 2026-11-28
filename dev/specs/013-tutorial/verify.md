# Verify: Tutorial for your first domain skill and your first pack

Run at 2026-10-06T02:00:49Z on commit `25393db`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 59 tests |
| Validate | `python3 scripts/aicfg.py validate` | pass |
| Tutorial | `specs/013-tutorial/run-tutorial.sh` (every bash block, fresh clone, temp HOME) | pass: "tutorial ran clean" |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | tutorial steps 1–6: clone, pack.toml with domains row, four-section skill, validate --pack, packs.local.toml, status/apply, tokens; all executed by the runner | pass |
| AC2 | each step has one bash block and a "you should see" line; the error example and in-sync line match real output | pass |
| AC3 | step 7 (git + CI snippet) and Next steps (example pack, packs.md, contributing to core) | pass |
| AC4 | `run-tutorial.sh` exit 0 on this commit; log in `.runs/tutorial-final.log` | pass |
| AC5 | README Adding content links the tutorial; VERSION 0.3.3; CHANGELOG entry; validate and tests pass | pass |

## Notes
- The runner is not in CI. The tutorial's requires_core pin ages at the next MINOR bump (follow-up).
