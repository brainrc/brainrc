# Plan: document the pack naming rules

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none here (gh:294 enforces them: [pack contract])
- **Security triggers touched:** none
- **Domains:** docs

## Files
| File | Change |
|---|---|
| `docs/packs.md` | modify |
| `tests/test_pack_naming.py` | new (gh:294 adds the docs-match-code test) |

## Tasks
- [x] **T1** [agent: doc-writer] add `## Naming` to docs/packs.md
  - files: `docs/packs.md`
  - criteria: AC1, AC2
