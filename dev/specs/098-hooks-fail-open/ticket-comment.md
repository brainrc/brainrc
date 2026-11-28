Guard hooks now skip a missing script instead of exiting 2, so a moved checkout or a Python upgrade no longer blocks every Claude Code tool call. Cursor's guard replies allow. `aicfg doctor` reports a hook that is missing, broken, or slow. Run `apply` to rewrite existing hook commands.
Verify: `python3 -m unittest -v tests.test_hooks.FailOpenTest tests.test_aicfg.DoctorTest`.
PR: <PR_URL>
