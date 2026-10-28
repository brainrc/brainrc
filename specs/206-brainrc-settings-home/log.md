# Log: 206-brainrc-settings-home

## engine · intake · done
2026-10-28T03:15:37Z
**Did:** Branch 206-brainrc-settings-home from main (v0.4.0, #230 merged). Size standard (config, cli, doctor, docs; a new `migrate` command and env var: contract change; migration of user files), mode subagent, domain scripting, offline only, auto false. Baseline below.
**Evidence:** baseline on main failed 6 tests (example pack requires_core <0.4 vs core 0.4.0, caused by #230's minor bump); fix PR #231 merged into this branch; baseline now 456 OK.
