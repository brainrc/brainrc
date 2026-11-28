# Plan: read CLAUDE_CONFIG_DIR for claude

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** additive: `${VAR:-default}` in harnesses.toml paths
- **Migrations / data changes:** none
- **Security triggers touched:** file writes into a path taken from the environment (only absolute values)
- **Domains:** scripting
- **Environments affected on deploy:** none (local CLI)
- **Destructive or replacing changes:** none

## Approach
Add `env_default` and `env_dir` to `brainrc/config.py`: `load_harnesses()` resolves each `${VAR:-default}` in a path once, so every consumer (plan, mcp, doctor, uninstall, manifest, hook commands) sees one concrete path. `claude_dir()` serves doctor's plugin checks. The manifest's trust check also accepts paths inside a dir a harness var names now.

## Files
| File | Change |
|---|---|
| `brainrc/config.py` | modify |
| `brainrc/doctor.py` | modify |
| `brainrc/manifest.py` | modify |
| `harnesses.toml` | modify |
| `tests/test_harness_env.py` | new |
| `tests/test_brainrc.py` | modify |
| `tests/test_doctor_home.py` | modify |
| `tests/test_doctor_plugin.py` | modify |
| `tests/test_migrate.py` | modify |
| `tests/test_settings_home.py` | modify |
| `scripts/check_tutorial.py` | modify |
| `specs/013-tutorial/run-tutorial.sh` | modify |

## Risks
- A var set in the shell but not where the harness runs sends files to the wrong dir; docs say to run brainrc with the harness's environment.

## Test strategy
`tests/test_harness_env.py`: the full command cycle per case (AC1 to AC3).

## Tasks
- [x] **T1** [agent: implementer] read CLAUDE_CONFIG_DIR for claude
  - files: `brainrc/config.py`, `brainrc/doctor.py`, `brainrc/manifest.py`, `harnesses.toml`, `tests/test_harness_env.py`, `tests/test_brainrc.py`, `tests/test_doctor_home.py`, `tests/test_doctor_plugin.py`, `tests/test_migrate.py`, `tests/test_settings_home.py`, `scripts/check_tutorial.py`, `specs/013-tutorial/run-tutorial.sh`
  - criteria: AC1, AC2, AC3, AC4, AC5
