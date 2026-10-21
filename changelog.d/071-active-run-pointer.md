---
bump: patch
---
- spec-agent records the active run's path in `$AICFG_HOME/active-run` (new `active_run.py write|read`) at intake, resume, and every checkpoint, so external tools can find the current run.
