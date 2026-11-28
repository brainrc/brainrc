# Plan: Reject duplicate pack names

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
`Source` gains `key` (its `packs.toml` table; `load_pack` already receives it as `name`). New
`sources.duplicate_packs(srcs)` returns one error per name used by two sources, core included,
naming the keys. `cli._sync`, `validate.cmd_validate`, and `doctor._doctor_sources` call it next
to their `collisions()` call; doctor's fix names `name` in `pack.toml` or `enabled = false`.

## Files
| File | Change |
|---|---|
| `aicfg/sources.py` | `Source.key`, `duplicate_packs` |
| `aicfg/cli.py`, `aicfg/validate.py`, `aicfg/doctor.py` | call it |
| `tests/test_aicfg.py` | `DuplicatePackTest` |

## Risks
- None beyond the spec's non-goals.

## Test strategy
`DuplicatePackTest(TempRepoCase)` with two scratch packs, through `cmd_validate`, `cmd_sync`, and `doctor_findings`.

## Tasks
- [ ] **T1** [agent: implementer] Refuse duplicate pack names
  - files: `aicfg/sources.py`, `aicfg/cli.py`, `aicfg/validate.py`, `aicfg/doctor.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC4
