# Plan: Validate accepts full model IDs and the Task tool

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none (validate accepts more)
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
`config.py`: add `Task` to `KNOWN_TOOLS` and a `MODEL_ID` pattern (`^claude-[a-z0-9][a-z0-9.-]*$`).
`validate._validate_source` accepts `meta["model"]` in `KNOWN_MODELS` or matching `MODEL_ID`.
`docs/formats.md` names the full-ID form.

## Files
| File | Change |
|---|---|
| `aicfg/config.py` | `Task`, `MODEL_ID` |
| `aicfg/validate.py` | model check uses `MODEL_ID` |
| `tests/test_aicfg.py` | `AgentFrontmatterTest` |
| `docs/formats.md` | agent `model` comment |

## Risks
- None.

## Test strategy
`AgentFrontmatterTest(TempRepoCase)`: rewrite one core agent's frontmatter and run `cmd_validate`.

## Tasks
- [ ] **T1** [agent: implementer] Accept full model IDs and `Task`
  - files: `aicfg/config.py`, `aicfg/validate.py`, `tests/test_aicfg.py`, `docs/formats.md`
  - criteria: AC1, AC2, AC3
