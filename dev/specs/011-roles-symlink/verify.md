# Verify: Supported platforms and a guarded roles symlink

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | README `### Platforms` under Install: macOS, Linux; Windows via WSL or Developer Mode + `core.symlinks true`; why | pass |
| AC2 | `RolesLinkTest` (plain file, wrong link, real repo); real `git clone -c core.symlinks=false`: first line is `ERROR skills/spec-agent/roles must be a symlink to ../../agents but is a plain file (cloned without symlink support?); enable symlinks (README, Platforms), then restore it with ...` | pass |
| AC3 | `DoctorTest.test_broken_roles_link` | pass |
| AC4 | `docs/formats.md` Agents section note with link to `README.md#platforms` | pass |
| AC5 | tests above, red first (3 assertion failures on a stub); VERSION 0.3.12, CHANGELOG | pass |

## Real run
In that clone, the message's fix (`git config core.symlinks true && git checkout -- skills/spec-agent/roles`)
restored the link and `validate` passed.

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK; `validate --pack examples/pack-acme` → OK
