Part 2 of 4 (epic #113) is ready for review. `validate` now runs on ubuntu, macOS and Windows across Python 3.11, 3.12 and 3.13. Windows cells are non-blocking (`continue-on-error`), and `scripts/check_tutorial.py` runs tutorial steps 1-5 in CI.
To verify: run `python3 scripts/check_tutorial.py` and `python3 -m unittest discover -s tests`, then check the 9 `validate` cells on the PR. ruff, pyright and coverage are not added and need owner approval.
PR: <PR_URL>
