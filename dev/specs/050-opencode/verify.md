# Verify: 050-opencode

| Criterion | Result | Evidence |
|---|---|---|
| AC1 render to `$AICFG_HOME/opencode/agents`, linked via `agents_format` | pass | `OpenCodeAgentTest.test_apply_links_rendered_agents`; fake-HOME apply links 9 agents to renders |
| AC2 conversion (denies, mode, no model) | pass | `test_tools_become_denies_and_model_is_dropped`, `test_agent_without_tools_keeps_every_permission` |
| AC3 prune and doctor | pass | `test_removed_agent_is_pruned`, `test_doctor_flags_a_stale_render`; doctor clean after apply |
| AC4 tests + real OpenCode | pass | OpenCode 1.18.35 `agent list`: all 9 as subagents; analyst denies bash, code-reviewer denies edit, implementer keeps edit and bash. Raw Claude agents made its config invalid (before) |
| AC5 docs, VERSION 0.3.19, CHANGELOG | pass | formats.md, spec-agent.md, harness-packages.md, roadmap, harnesses.toml comments |

Also: 138 tests OK (new ones red first), validate core + acme OK, `claude plugin validate .` OK,
tutorial OK. Not run: #19's E2E sandbox ticket in OpenCode (needs a model provider login).
