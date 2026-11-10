# Plan: apply validates packs before linking

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
New `validate.pack_errors(srcs)`: the agent and skill names of every source, then
`_validate_source` for each pack (not core), the same per-source checks `validate --pack` runs.
`cli._sync` calls it after the `requires_core` check and before anything is written; on errors
it prints them and "Nothing written. Fix the pack (`validate --pack <dir>` lists every
problem), then re-run." and returns 1.

## Files
| File | Change |
|---|---|
| `aicfg/validate.py` | `pack_errors` |
| `aicfg/cli.py` | `_sync` calls it |
| `tests/test_aicfg.py` | `PackApplyCheckTest` |

## Risks
- A pack with any validate error now blocks apply (the gate's choice); doctor already fails it.

## Test strategy
`PackApplyCheckTest(TempRepoCase)` with a scratch pack, through `cmd_sync(False)` and `cmd_sync(True)`.

## Tasks
- [ ] **T1** [agent: implementer] apply and status refuse a pack validate would fail
  - files: `aicfg/validate.py`, `aicfg/cli.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC4
