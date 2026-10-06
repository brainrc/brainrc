# Verify: Sandbox E2E fixes

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `SandboxSetupTest` runs the README's bash block verbatim: `git status --short` empty after tests (red before: stale `__pycache__` committed and modified) | pass |
| AC2 | same test: `.env` not in `git ls-files`, its value in no commit, 32 hex chars | pass |
| AC3 | `CanaryTest`: clean run passes; canary in a commit on another branch fails; in ignored `specs/.../.runs/T1.log` fails; missing decoy fails naming the README; value never printed | pass |
| AC4 | #18 sandbox run with a decoy added: `sandbox-002` 11 passed, 0 failed; a copy of `.env` in `.runs/leak.log` → canary FAIL | pass |
| AC5 | `test_main_untouched_pass_message` | pass |
| AC6 | `docs/evals.md` table row; `VERSION` 0.3.6; CHANGELOG 0.3.6; `validate` OK | pass |

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK: 21 skills, 9 agents, 5 commands
- `python3 scripts/aicfg.py validate --pack examples/pack-acme` → OK
