Shipped (child 1 of 6 of #241): each spec-agent run works in its own git worktree at `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`. Your checkout is not touched, and a run stops if the checkout has the run's branch checked out. `/spec-resume` and `/spec-status` find runs through `state.worktree`.
Verify: `python3 -m unittest discover -s tests -p 'test_run_worktree.py'` and `-p 'test_active_run.py'`. The model-driven `/work` and `/spec-resume` runs (AC1, AC3, AC7) are not run end to end yet.
PR: https://github.com/brainrc/brainrc/pull/257
