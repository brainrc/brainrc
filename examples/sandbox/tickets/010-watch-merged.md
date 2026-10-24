---
id: 10
title: Add a --version flag (watch a merged PR)
status: open
pr:
---
Add `--version` to `greet.py`: it prints `greet 1.0` and exits 0. Add a test in `test_greet.py`.
Meant for the watch stage: run with `SPEC_PR_STATUS_FIXTURE=pr_status/merged.json`
(see `evals/cases/sandbox-007.toml`). The fixture reports the PR merged: watch verifies the merge
commit, writes `verify-merged.md`, appends `## After delivery` to `retro.md`, and ends at `stage: done`.
