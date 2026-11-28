# Plan: read XDG_CONFIG_HOME for opencode

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** file writes into a path taken from the environment (only absolute values)
- **Domains:** scripting
- **Environments affected on deploy:** none (local CLI)
- **Destructive or replacing changes:** none

## Approach
Playbook step 1 for the `[opencode]` paths, plus `mcp_file()` in `brainrc/mcp.py`: when `opencode.json` doesn't exist and `opencode.jsonc` does, that is the MCP file. A new stdlib `brainrc/jsonc.py` reads JSONC and replaces one top-level key in place; the merge re-parses the result and refuses (state `invalid`) unless it matches. Uninstall uses the same `mcp_file()`.

## Files
| File | Change |
|---|---|
| `brainrc/jsonc.py` | new |
| `brainrc/mcp.py` | modify |
| `brainrc/uninstall.py` | modify |
| `harnesses.toml` | modify |
| `tests/test_harness_env.py` | modify |
| `docs/formats.md` | modify |
| `docs/install.md` | modify: the three vars, once all are in |

## Risks
- A var set in the shell but not where the harness runs sends files to the wrong dir; docs say to run brainrc with the harness's environment.

## Test strategy
`tests/test_harness_env.py`: the full command cycle per case (AC1 to AC3), the jsonc merge and parser.

## Tasks
- [x] **T1** [agent: implementer] read XDG_CONFIG_HOME for opencode
  - files: `brainrc/jsonc.py`, `brainrc/mcp.py`, `brainrc/uninstall.py`, `harnesses.toml`, `tests/test_harness_env.py`, `docs/formats.md`, `docs/install.md`
  - criteria: AC1, AC2, AC3, AC4, AC5
