`validate` now accepts an agent `model` given as a full Claude model ID (`claude-sonnet-5-5`) and `Task` in `tools`. Other names still fail.
Verify: `python3 -m unittest -v tests.test_aicfg.AgentFrontmatterTest`.
PR: <PR_URL>
