# Verify: Troubleshooting doc

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `docs/troubleshooting.md` opens with `doctor`, then sections for missing items, `CONFLICT`, pack errors, settings backups, uninstall, and guard hook reports | pass |
| AC2 | Each pack message reproduced in a scratch copy with real packs (collision, prefix, bad prefix, `requires_core`, missing `pack.toml`); `BACKUPS_KEPT = 5` and `.bak-aicfg-<stamp>` from the code; uninstall steps run in a fake HOME: 0 links left, 2 hook entries left as documented, oldest backup restores `{"theme": "dark"}` | pass |
| AC3 | README links it after the doctor paragraph and in the layout list; `test_points_to_troubleshooting_only_when_something_is_wrong` (red first: pointer missing) | pass |
| AC4 | VERSION 0.3.8, CHANGELOG 0.3.8; `validate` OK | pass |

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK; `validate --pack examples/pack-acme` → OK

## Corrections made while verifying
- The collision example now uses two packs (core and a prefixed pack can't collide in practice).
- "apply writes nothing" was true only for collisions and `requires_core`; the doc now says so.
