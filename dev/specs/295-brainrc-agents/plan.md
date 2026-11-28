# Plan: core agents under brainrc-

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** agent names (old names kept as aliases); `extensions.domains.reviewer`
  accepts both
- **Security triggers touched:** none (aliases copy their target's tools exactly, and validate checks it)
- **Domains:** scripting, docs

## Approach
`git mv` each agent and fix its `name`; write a stub alias per old name; add `check_core_agents` to
`brainrc/naming.py` and run it for core; rename the references that name an agent (role links, backticked
names, `[agent: ...]`, the Domains reviewer column, `reviewer = ...`, agent paths).

## Files
| File | Change |
|---|---|
| `agents/*.md` | rename, new aliases |
| `brainrc/naming.py`, `brainrc/validate.py` | modify |
| `skills/spec-agent/SKILL.md`, `references/*.md`, `templates/plan.md` | modify (names only) |
| `docs/*.md`, `examples/pack-acme/pack.toml` | modify (names only) |
| `tests/test_agent_aliases.py` | new |
| `tests/test_brainrc.py`, `tests/test_planning.py` | modify |

## Tasks
- [x] **T1** [agent: implementer] rename, aliases, validate check, references
  - files: as above
  - criteria: AC1, AC2, AC3, AC4
