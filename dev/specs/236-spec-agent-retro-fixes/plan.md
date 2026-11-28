# Plan: spec-agent fixes from the rename campaign's retros

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none (validate gains an error that only fires on a premature removal bump)
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
`release.check_fragments` already parses every fragment for validate and release; it now also
compares the largest bump's next version with `cli.SHIM_REMOVED_IN` (imported lazily; `cli`
imports `release`). `TempRepoCase` clears `XDG_CONFIG_HOME`. Three one-sentence rules go in
SKILL.md § Auto mode, handoff.md § Dispatch prompt, and agents/analyst.md.

## Files
| File | Change |
|---|---|
| `brainrc/release.py`, `tests/test_brainrc.py` | removal-release check, tests, XDG isolation |
| `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/handoff.md`, `agents/analyst.md` | rules |
| `changelog.d/236-spec-agent-retro-fixes.md` | fragment |

## Risks
- None beyond a false positive on a deliberate 0.5.0 bump, which removing `SHIM_REMOVED_IN` clears.

## Test strategy
AC1 by ReleaseTest (red first); AC2 by the suite passing with `XDG_CONFIG_HOME` set; AC3 by reading.

## Tasks
- [x] **T1** [agent: implementer] Removal-release check and XDG isolation
  - files: `brainrc/release.py`, `tests/test_brainrc.py`, `changelog.d/236-spec-agent-retro-fixes.md`
  - criteria: AC1, AC2
- [x] **T2** [agent: implementer] Three spec-agent rules
  - files: `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/handoff.md`, `agents/analyst.md`
  - criteria: AC3
