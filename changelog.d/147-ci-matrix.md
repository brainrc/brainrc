---
bump: patch
---
- CI: `validate` now runs on ubuntu, macOS and Windows across Python 3.11, 3.12 and 3.13 (fail-fast off). Windows cells are reported but non-blocking, since Windows is unsupported natively. Gitleaks runs once, in the ubuntu 3.12 cell.
- CI: a final gate job keeps the `validate` check name, so branch protection on `validate` still works; it passes only when all blocking cells pass.
- CI: a new step runs `scripts/check_tutorial.py`, which executes steps 1-5 of `docs/tutorial.md` and fails with the step name when a documented command or output breaks.
- ruff, pyright and coverage are deferred pending owner approval of the new dependencies.
