# Plan: Core version contract for packs, and a CHANGELOG

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none (stdlib only)
- **Public API / contract changes:** new optional top-level `pack.toml` key `requires_core`;
  new root file `VERSION`. Existing packs keep working (warning only).
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none; takes effect on the next `aicfg apply` per machine
- **Destructive or replacing changes:** none

## Approach
`VERSION` (repo root, `0.1.0`) is the single source of truth. `aicfg.py` gains three small
helpers next to the pack loading code: `core_version()` reads `REPO / "VERSION"` at call time (so
tests that repoint `aicfg.REPO` work) and raises `ConfigError` if it isn't `MAJOR.MINOR.PATCH`;
`parse_constraint(text)` turns `">=0.1, <0.2"` into `[(op, (0,1,0)), ...]` (versions may omit
trailing parts; a bare version means `>=`; anything else raises `ValueError` with the accepted
syntax); `pack_compat(src, core)` returns `(errors, warnings)` for one pack.

Both entry points reuse `pack_compat`: `_validate_pack` appends its errors (so plain `validate`
and `validate --pack` behave the same), and `cmd_validate` adds a `core_version()` failure as an
error and prints warnings as `WARN` lines. `cmd_sync` checks enabled packs right after the existing
`collisions()` check and refuses in exactly the same way ("Nothing written"), which covers both
`status` and `apply` and never touches disabled packs (`sources()` doesn't load them).

Design choice: tuple comparison over a hand-rolled parser rather than `packaging` (stdlib rule)
or a regex-only check (can't express ranges). Pre-release tags are out of scope.

## Files
| File | Change |
|---|---|
| `VERSION` | new: `0.1.0` |
| `scripts/aicfg.py` | modify: helpers, validate + sync checks, docstring |
| `tests/test_aicfg.py` | modify: copy `VERSION` in `copy_repo`, fixture gets `requires_core`, new tests |
| `CHANGELOG.md` | new: 0.1.0 entry with history from the roadmap; `[pack contract]` marker |
| `docs/roadmap.md` | modify: replace the Done line with a link to the CHANGELOG |
| `docs/packs.md` | modify: `requires_core` in the example, syntax, compatibility policy |
| `README.md` | modify: layout lists `VERSION` and `CHANGELOG.md` |

## Risks
- Existing `"Everything in sync."` test breaks on the new warning, mitigated by adding
  `requires_core` to the shared fixture and testing the missing case separately.
- `copy_repo` doesn't copy root files besides `harnesses.toml`, mitigated by copying `VERSION`.

## Test strategy
Unit tests in `tests/test_aicfg.py`: `parse_constraint` / satisfaction table (pass, fail, padding,
bare version, malformed); `PackValidateTest` for compatible, incompatible, missing (warning),
malformed, and invalid `VERSION`; `PackSyncTest` for incompatible → exit 1 and an empty HOME,
and disabled incompatible pack → apply succeeds.

## Tasks
- [ ] **T1** [agent: test-writer] Contract tests for version parsing and pack compatibility
  - files: `tests/test_aicfg.py`
  - criteria: AC2, AC3, AC4, AC5, AC6, AC7, AC10
  - review: each
- [ ] **T2** [agent: implementer] `VERSION`, helpers, and validate checks (passes T1's validate tests)
  - files: `VERSION`, `scripts/aicfg.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC5, AC6
  - review: each
- [ ] **T3** [agent: implementer] Refuse incompatible packs in `status`/`apply` (passes T1's sync tests)
  - files: `scripts/aicfg.py`, `tests/test_aicfg.py`
  - criteria: AC4, AC7
- [ ] **T4** [agent: implementer] CHANGELOG, roadmap, packs docs, README layout
  - files: `CHANGELOG.md`, `docs/roadmap.md`, `docs/packs.md`, `README.md`
  - criteria: AC8, AC9
