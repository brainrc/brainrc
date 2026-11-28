# Verify: Example pack validated in CI

Run at 2026-10-05T13:20:37Z on commit `1ad5d4a`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 47 tests (46 before) |
| Validate (core) | `python3 scripts/aicfg.py validate` | pass: 20 skills, 9 agents, 5 commands (unchanged) |
| Validate (example) | `python3 scripts/aicfg.py validate --pack examples/pack-acme` | pass, no WARN |
| Sandbox | `python3 -m unittest -q` in `examples/sandbox` | pass |
| actionlint / zizmor | — | not installed: CI step verified after push |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `validate --pack examples/pack-acme` → OK, no warnings; `ExamplePackTest` | pass |
| AC2 | `pack.toml` has `requires_core` + domains, intake_context, ticket, deliver_checks; skills `acme-deploy`, `acme-context`; rule; command; one tripwire. Manual `apply` in temp HOME: skills, command, rule linked and all four extensions rendered in `extensions.md` | pass |
| AC3 | `examples/pack-acme/README.md`: copy, rename, `requires_core`, enable, apply, validate in pack CI | pass |
| AC4 | Mutation: `VERSION` 0.2.0 → `ExamplePackTest` fails with `requires_core ... not satisfied by core 0.2.0` (reverted). Tripwire fires on a non-allowed line (reverted) | pass |
| AC5 | Step "Validate example pack" in `.github/workflows/validate.yml` | verify after push: `validate` job |
| AC6 | `docs/packs.md` intro links to `examples/pack-acme/README.md` | pass |
| AC7 | Core validate counts unchanged; manual apply without the pack unaffected (example only linked when listed in `packs.local.toml`) | pass |

## Notes
- Two prefixed skills, not one: approved plan deviation (intake_context needs its own skill).
