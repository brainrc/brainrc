spec-agent now writes the active run's absolute path to `$AICFG_HOME/active-run` at intake, on resume, and at every checkpoint. The file contract is in `skills/spec-agent/references/state.md` (§ Active run pointer).
Verify: `python3 -m unittest discover -s tests -p test_active_run.py -v`. The agent-orchestration mod still needs to read the pointer. It is outside this repo.
PR: https://github.com/bxker/ai-config/pull/72
