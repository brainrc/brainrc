An installed `aicfg` now copies core's guard hooks to `$AICFG_HOME/hooks/core/` and links them from there. A real upgrade from Python 3.12 to 3.13, with the old venv deleted and no re-apply, still got `ask` from Claude's guard and `deny` from Cursor's. `status` flags a stale copy, and `apply` refreshes it.
Verify: `python3 -m unittest -v tests.test_aicfg.InstalledModeTest`.
PR: <PR_URL>
