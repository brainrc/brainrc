Accept full Claude model IDs and the Task tool in agents

5 of 5 in epic #93 (E2: Config and pack loading).

## Why
`validate` accepted an agent's `model` only as `haiku`, `sonnet`, `opus`, or `inherit`, so a pack agent pinned to a full Claude model ID such as `claude-sonnet-5-5` failed, even though Claude Code accepts it. `tools: Task`, the subagent tool that the OpenCode renderer already maps to `task`, was reported as an unknown tool.

## What changed
- `config.KNOWN_TOOLS` includes `Task`. The new `config.MODEL_ID` (`^claude-[a-z0-9][a-z0-9.-]*$`) is accepted next to the aliases in `validate`'s agent check.
- `docs/formats.md` shows the full-ID form. The `aicfg-config` living spec gets "Agent model and tool names".

## Acceptance criteria
- [x] AC1: full `claude-` model IDs validate, verified by `AgentFrontmatterTest.test_full_claude_model_id_is_accepted`
- [x] AC2: `tools: Task` validates, verified by `test_task_tool_is_accepted`
- [x] AC3: other model and tool names still fail, verified by `test_unknown_names_still_fail`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
```

## Follow-ups
- Bedrock and Vertex model IDs (`us.anthropic.claude-…`, `claude-…@date`) still fail validation.

Spec: `specs/202-validate-model-ids-task-tool/spec.md` · Plan: `specs/202-validate-model-ids-task-tool/plan.md`
Closes #202
