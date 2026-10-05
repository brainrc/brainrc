# Plan: Apply the first five retros to spec-agent

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none for packs. `state.json` gains optional
  `metrics.gates.<gate>.presented_at|approved_at`; resume tolerates their absence.
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** none (docs and agent instructions)
- **Environments affected on deploy:** none; takes effect when spec-agent next runs
- **Destructive or replacing changes:** none

## Approach
Each retro item goes where the engine or role already looks at that moment, as one or two
lines, so nothing new loads by default:
- **AC1** `references/sizing.md`: a "Changed lines" note under the table. ~30 lines with no
  design choice caps at `small`; new self-contained example/doc files weigh about half. Floors
  still apply.
- **AC2** `references/lifecycle.md` § Gate presentation: the Deliver gate adds a `Changes:`
  line (diff stat outside `specs/`) above `Artifacts:`.
- **AC3** `references/lifecycle.md` intake: new step 3 before branching. If `VERSION` exists,
  list open PRs touching `VERSION`/`CHANGELOG.md` through the connector's system and recommend
  waiting. Deliver re-checks before pushing.
- **AC6** same intake list, at the mode step: say "fallback" out loud when the harness has
  subagents but the named agents aren't installed, and point to `aicfg apply`.
- **AC4** `references/state.md` schema + rules, `SKILL.md` Run steps 3–4 (one clause each),
  `templates/retro.md` (agent time vs gate wait).
- **AC5** `agents/code-reviewer.md` § Check, item 2 extended.

## Files
| File | Change |
|---|---|
| `skills/spec-agent/references/sizing.md` | changed-lines guidance |
| `skills/spec-agent/references/lifecycle.md` | intake VERSION check, fallback notice, Deliver gate `Changes:` |
| `skills/spec-agent/references/state.md` | gate timestamps in schema and rules |
| `skills/spec-agent/SKILL.md` | record gate timestamps in Run steps |
| `skills/spec-agent/templates/retro.md` | agent time vs wait time |
| `agents/code-reviewer.md` | messages vs docs |
| `VERSION`, `CHANGELOG.md` | 0.3.1 |

## Risks
- Engine prompt grows, mitigated by one-to-two-line edits; check `aicfg tokens` before/after.

## Test strategy
Docs only: `validate` (links, references) and the suite. Manual: read each changed section
against its AC.

## Tasks
- [ ] **T1** [agent: implementer] Sizing by changed lines
  - files: `skills/spec-agent/references/sizing.md`
  - criteria: AC1
- [ ] **T2** [agent: implementer] Intake VERSION check, fallback notice, Deliver gate changes line
  - files: `skills/spec-agent/references/lifecycle.md`
  - criteria: AC2, AC3, AC6
- [ ] **T3** [agent: implementer] Gate timestamps and retro timing
  - files: `skills/spec-agent/references/state.md`, `skills/spec-agent/SKILL.md`, `skills/spec-agent/templates/retro.md`
  - criteria: AC4
- [ ] **T4** [agent: implementer] Reviewer messages-vs-docs check, 0.3.1 release
  - files: `agents/code-reviewer.md`, `VERSION`, `CHANGELOG.md`
  - criteria: AC5, AC7
