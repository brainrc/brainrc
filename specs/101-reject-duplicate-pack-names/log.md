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
