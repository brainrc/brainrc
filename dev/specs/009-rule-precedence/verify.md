# Verify: Explicit rule precedence across core, packs, and local rules

Run at 2026-10-05T15:22:32Z on commit `4d01a90`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 55 tests (47 before) |
| Validate (core) | `python3 scripts/aicfg.py validate` | pass |
| Validate (example) | `python3 scripts/aicfg.py validate --pack examples/pack-acme` | pass |
| Sandbox | `python3 -m unittest -q` in `examples/sandbox` | pass |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `RenderInstructionsTest`; manual `apply` with the example pack and a local rule in a temp HOME: core headings (lines 3–39), then `<!-- pack: acme -->` (48), then `<!-- local -->` (56) | pass |
| AC2 | `test_pack_rules_follow_every_core_rule` (pack `15-acme.md` after the last core rule) | pass |
| AC3 | `test_pack_blocks_are_labelled_in_source_order`, `test_local_rules_render_last_under_a_label` | pass |
| AC4 | `test_core_only_render_is_unchanged`; manual: core-only render equals `main`'s `render_instructions` output (True) | pass |
| AC5 | `docs/formats.md` Rules section and new `docs/packs.md` Rules section state order and policy | pass |
| AC6 | `## 0.2.0` tagged [pack contract]; `VERSION` 0.2.0; example pin `>=0.2, <0.3` (old pin fails `ExamplePackTest` at 0.2.0, reverted) | pass |
| AC7 | `ChangelogCheckTest`: match passes; mismatch, Unreleased, and missing heading each fail with the named message | pass |
| AC8 | suite, validate, example validate all pass | pass |

## Notes
- #30 (0.1.2) is open. Whichever of #30 and this PR merges second takes a CHANGELOG/VERSION merge. This PR stays 0.2.0.
