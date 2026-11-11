# Plan: Reserved skill names check in validate

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none (a new validate error for core only)
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Add `RESERVED_SKILL_NAMES` next to `DEPRECATED_ALIASES` in `brainrc/validate.py`, and in the core
branch of `_validate_source` report each core skill whose name is reserved and not an alias.

## Files
| File | Change |
|---|---|
| `brainrc/validate.py` | modify: constant and check |
| `tests/test_reserved_names.py` | new |
| `changelog.d/149-2-reserved-names.md` | new, patch |

## Risks
- The list is a belief, not a verified harness list. It is one constant.

## Test strategy
Temp-repo tests (`TempRepoCase`): a core `skills/init` fails naming it; the shipped copy passes; a pack skill named `status` passes this check; core + pack duplicate still errors.

## Tasks
- [ ] **T1** [agent: implementer] Reserved-name check
  - files: `brainrc/validate.py`, `tests/test_reserved_names.py`, `changelog.d/149-2-reserved-names.md`
  - criteria: AC1, AC2, AC3
