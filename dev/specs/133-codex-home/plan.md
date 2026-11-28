# Plan: read CODEX_HOME for codex

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none (local CLI)
- **Destructive or replacing changes:** none

## Approach
Playbook step 1 only: the four `[codex]` paths become `${CODEX_HOME:-~/.codex}/...`. The resolver from gh:132 does the rest.

## Files
| File | Change |
|---|---|
| `harnesses.toml` | modify |
| `tests/test_harness_env.py` | modify |

## Risks
- A var set in the shell but not where the harness runs sends files to the wrong dir; docs say to run brainrc with the harness's environment.

## Test strategy
`tests/test_harness_env.py`: the full command cycle per case (AC1 to AC3).

## Tasks
- [x] **T1** [agent: implementer] read CODEX_HOME for codex
  - files: `harnesses.toml`, `tests/test_harness_env.py`
  - criteria: AC1, AC2, AC3, AC4
