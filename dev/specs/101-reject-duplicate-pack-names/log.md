# Log: 101-reject-duplicate-pack-names

## engine · intake · done
2026-10-27T02:27:18Z

**Did:** Child 2 of campaign gh:93. Branch 101-reject-duplicate-pack-names from 100-readable-config-errors (20aa71f). ticket.md from gh:101. Size small (sources.py + tests, behavior clear), mode inline, domains: scripting, offline only.

**Evidence:**
- reproduced on a scratch copy: two packs named `acme` → `validate` OK (`packs: acme, acme`); a pack named `core` → unrelated `overrides/opencode/plugin.js` error

**Changed files:** specs/101-reject-duplicate-pack-names/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-27T02:27:18Z

**Did:** Wrote spec.md: 4 criteria (duplicate names in validate/status/apply, doctor, a pack named core, key≠name is fine). Adds one requirement to aicfg-config.

**Evidence:**
- `living_specs.py check` → would update specs/living/aicfg-config.md

**Changed files:** specs/101-reject-duplicate-pack-names/spec.md

**Open issues:** none

**Next:** Spec gate

## engine · Spec gate approved
2026-10-27T02:30:50Z

- Spec approval time not recorded (left unset rather than estimated).

## implementer · T1 · done
2026-10-27T02:30:50Z

**Did:** `Source.key`; `duplicate_packs()` in sources.py; called by `_sync`, `cmd_validate`, `_doctor_sources` (FAIL with a pack.toml / enabled fix). Self-review: `validate --pack` on a pack named core said "core and core"; label key-less packs by their dir (test added).

**Evidence:**
- red: 3 of 4 new tests failed on assertions (validate OK with `packs: acme, acme`)
- `python3 -m unittest discover -s tests` → 413 passed

**Changed files:** aicfg/sources.py, aicfg/cli.py, aicfg/validate.py, aicfg/doctor.py, tests/test_aicfg.py

**Open issues:** none

**Next:** verify

## verifier · verify · done
2026-10-27T02:30:50Z

**Did:** verify.md on d40a193: AC1-AC4 pass, manual run on a scratch copy.

**Evidence:**
- `python3 -m unittest discover -s tests` → 413 passed; `validate` OK

**Changed files:** specs/101-reject-duplicate-pack-names/verify.md

**Open issues:** none

**Next:** document

## doc-writer · document · done
2026-10-27T02:30:50Z

**Did:** living delta applied (aicfg-config: Unique pack names), troubleshooting row, changelog fragment, pr-body.md, ticket-comment.md.

**Evidence:**
- `living_specs.py apply` → updated specs/living/aicfg-config.md; `validate` OK

**Changed files:** docs/troubleshooting.md, changelog.d/101-reject-duplicate-pack-names.md, specs/living/aicfg-config.md, drafts

**Open issues:** none

**Next:** child 2 verified; child 3 gh:102
