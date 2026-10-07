# Verify: spec-agent retro improvements (round 2)

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `agents/verifier.md` Method step 4: real run in a scratch copy, fresh `HOME`, no deletes through `$HOME` | pass |
| AC2 | `agents/implementer.md` Method step 1: switch off only the new change when code exists | pass |
| AC3 | `references/lifecycle.md` stage 7: push the done checkpoint after CI on the delivered commit | pass |
| AC4 | `references/sizing.md`: test lines count about half | pass |
| AC5 | VERSION 0.3.10, CHANGELOG 0.3.10; `validate` OK (core and pack); tests OK | pass |

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK; `validate --pack examples/pack-acme` → OK
- `python3 scripts/aicfg.py tokens`: verifier 585 on use, implementer 540 (each +~30)

No red test: prose-only change to agent and reference files, which `validate` covers.
