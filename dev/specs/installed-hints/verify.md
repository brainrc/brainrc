# Verify: installed-hints

| Criterion | Result | Evidence |
|---|---|---|
| AC1 installed hints and usage say `aicfg`; checkout unchanged | pass | `test_hints_name_the_installed_command` (red first); real `uv tool install`: doctor prints `fix: aicfg apply` ×13, usage `aicfg status`; checkout transcript identical to 0.3.23 |
| AC2 plugin hints unchanged | pass | aicfg/plugin.py untouched |
| AC3 test, README, CHANGELOG, VERSION 0.3.24 | pass | 160 tests OK; validate, tutorial, `claude plugin validate` OK |
