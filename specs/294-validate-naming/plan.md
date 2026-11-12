# Plan: validate enforces the pack naming rules

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** [pack contract] new optional `pack.toml` key `id`; packs that broke
  a rule now fail `validate` and `apply` (bump minor)
- **Security triggers touched:** none
- **Domains:** scripting

## Approach
A new module, `brainrc/naming.py`, holds the official IDs, the vendor list and one check per pack.
`_validate_pack` calls it in place of its two name and prefix checks; rule 7 stays where it was.

## Files
| File | Change |
|---|---|
| `brainrc/naming.py` | new |
| `brainrc/validate.py` | modify |
| `tests/test_pack_naming.py` | new |
| `docs/packs.md`, `examples/pack-acme/pack.toml`, `examples/pack-acme/README.md` | modify (`id`) |

## Tasks
- [x] **T1** [agent: implementer] naming checks, wired into validate, near-miss tests
  - files: as above
  - criteria: AC1 to AC7
