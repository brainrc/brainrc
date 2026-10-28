# Verify: Rename the PyPI package and the command to brainrc

Run at 2026-10-28T02:38:17Z on commit `c2c9e56`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 456 tests, OK |
| Lint | not configured (actionlint, zizmor not installed) | not configured |
| Build | `pip install /home/user/brainrc` into a fresh venv outside the repo | pass: brainrc 0.3.50 installed |
| Validate (infra) | `python3 scripts/brainrc.py validate`; `... --pack examples/pack-acme`; sandbox `python3 -m unittest -q`; `scripts/brainrc.py plugin` | pass: OK (26 skills, 9 agents); pack OK; sandbox 2 OK; manifests unchanged |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | fresh venv: `brainrc --version` → `brainrc 0.3.50`, exit 0; `check_install.py` PASS AC1; unit test in tests/test_aicfg.py | pass |
| AC2 | `check_install.py` PASS AC2 (dist `brainrc`, entry points `brainrc = brainrc.cli:entry`, `aicfg = brainrc.cli:deprecated_entry`); pyproject tomllib test | pass |
| AC3 | `check_install.py` PASS AC3 (`aicfg status` same stdout/exit as `brainrc status`, exit 0, one stderr line); tests/test_cli_entry_points.py AC3 tests | pass |
| AC4 | tests/test_cli_entry_points.py `test_ac4_scripts_brainrc_validate_has_no_warning`; `scripts/brainrc.py validate` exit 0 | pass |
| AC5 | `scripts/aicfg.py validate --pack examples/pack-acme` exit 0 with one warning naming `scripts/brainrc.py`; `test_ac5_...` | pass |
| AC6 | `check_install.py` PASS AC6 (`-m brainrc` and `-m aicfg` status match, one warning for aicfg only); `test_ac6_...` | pass |
| AC7 | `check_install.py` PASS AC7; `test_ac7_import_aicfg_emits_deprecation_warning`, `test_ac7_aicfg_cli_main_is_brainrc_cli_main` | pass |
| AC8 | `check_install.py` PASS AC8 (bundled `_core` contents, `installed()` true, `brainrc validate` outside a checkout) | pass |
| AC9 | `scripts/brainrc.py nosuchcmd` prints usage naming `brainrc`, no `aicfg.py`, exit 2; `test_usage_names_brainrc_in_a_checkout`, `..._when_installed` | pass |
| AC10 | suite, validate, and every command both workflows run, run locally with the new names (above); the workflows themselves run on push | pass (workflows re-checked by CI after push) |
| AC11 | `test_ac11_*` (4 tests, including `-W default -m aicfg`): one warning, stderr only | pass |

## Notes
- The wheel was built and installed locally (PyPI reachable). CI repeats `check_install.py` after `pip install .`.
- `check_install.py` refuses a `pip install --user` install (scripts outside the interpreter's scripts dir); CI uses a normal install.
- Not covered here: upgrading over an old `ai-config` install (both ship `aicfg`); the changelog fragment tells users to uninstall `ai-config` first.
