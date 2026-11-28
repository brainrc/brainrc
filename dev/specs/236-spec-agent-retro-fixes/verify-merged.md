# Verify: Post-merge verify of 6d0bd02 (merge commit of #236, from origin/main)

Run at 2026-10-29T04:50:00Z on commit `7e758d4` (main after release v0.5.0, which contains 6d0bd02).

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (also with `XDG_CONFIG_HOME=/home/runner/.config`) | pass: OK (1 skipped) both ways |
| Lint | not configured | not configured |
| Build | `pip install .` in a fresh venv, then `scripts/check_install.py` | pass: every check PASS |
| Validate (infra) | `python3 scripts/brainrc.py validate`; `validate --pack examples/pack-acme` | pass |
| Plan / diff | `specs/013-tutorial/run-tutorial.sh` | pass: tutorial ran clean |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| all | suite (including test_old_names), validate, the install check and the tutorial pass on main | pass |

## Notes
Release v0.4.6 (2c27a54) followed the merge. `brainrc --version` prints `brainrc 0.5.0` on main.
