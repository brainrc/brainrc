---
id: 8
title: Add a --version flag (watch a red CI run)
status: open
pr:
---
Add `--version` to `greet.py`: it prints `greet 1.0` and exits 0. Add a test in `test_greet.py`.
Meant for the watch stage: run with `SPEC_PR_STATUS_FIXTURE=pr_status/red-ci.json`
(see `evals/cases/sandbox-005.toml`). The fixture's failing `unit-tests` log names `greet.py`, a
file this change touches, so the failure is classified as own and gets a fix task.
