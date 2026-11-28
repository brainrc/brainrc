# Log: 102-apply-validates-packs

## engine · intake · done
2026-10-27T02:31:40Z

**Did:** Child 3 of campaign gh:93. Branch 102-apply-validates-packs from 101-reject-duplicate-pack-names. ticket.md from gh:102. Size small (cli.py, validate.py, tests; ~30 lines), mode inline, domains: scripting, offline only.

**Evidence:**
- reproduced on a scratch copy: pack `acme` with `skills/deploy` → `apply` exit 0, `~/.claude/skills/deploy` linked; `validate` FAILED with the prefix error

**Changed files:** specs/102-apply-validates-packs/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-27T02:31:40Z

**Did:** Wrote spec.md: 4 criteria (apply and status refuse a failing pack, any pack error blocks, passing packs unchanged). Adds "Apply checks packs first" to aicfg-config.

**Evidence:**
- `living_specs.py check` (below)

**Changed files:** specs/102-apply-validates-packs/spec.md

**Open issues:** 1 (which checks block apply; default all)

**Next:** Spec gate

## engine · Spec gate approved
2026-10-27T02:32:52Z

- Open question 1 resolved with its default (every check). Spec change after approval (wording only): marked resolved.

## implementer · T1 · done
2026-10-27T02:35:14Z

**Did:** `validate.pack_errors()` (per-pack `_validate_source`), called in `_sync` before writing; hint names only failing packs (self-review fix, test added).

**Evidence:**
- red: 2 new tests failed on assertions (apply exit 0)
- `python3 -m unittest discover -s tests` → 417 passed

**Changed files:** aicfg/validate.py, aicfg/cli.py, tests/test_aicfg.py

**Open issues:** none

**Next:** verify

## verifier · verify · done
2026-10-27T02:35:14Z

**Did:** verify.md on 58622e4: AC1-AC4 pass; manual scratch run (refused, then linked after the rename).

**Evidence:**
- `python3 -m unittest discover -s tests` → 417 passed; `validate` OK

**Changed files:** specs/102-apply-validates-packs/verify.md

**Open issues:** none

**Next:** document

## doc-writer · document · done
2026-10-27T02:35:14Z

**Did:** living delta (aicfg-config: Apply checks packs first), troubleshooting wording, changelog fragment, drafts.

**Evidence:**
- `living_specs.py apply` → updated; `validate` OK

**Changed files:** docs/troubleshooting.md, changelog.d/102-apply-validates-packs.md, specs/living/aicfg-config.md, drafts

**Open issues:** none

**Next:** child 3 verified; child 4 gh:103
