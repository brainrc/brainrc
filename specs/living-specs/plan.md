# Plan: living specs

Spec: approved (truth in `specs/living/`; deltas applied by the script) · Mode: inline · Domains: scripting

## Formats
Delta, in `spec.md`:
```
## Requirement changes
### Area: cli
Purpose: <one line; used only when the area file is new>
#### ADDED: Shout flag
The CLI SHALL print the greeting in upper case when `--shout` is given. (AC1)
#### MODIFIED: Default greeting
<full new text>
#### REMOVED: Old flag
Why: <reason>
```
or `None` under the heading. Truth, `specs/living/<area>.md`: `# <area>`, the purpose line,
then `### <requirement>` blocks ending `_Last changed by <slug>._`

| Task | What | Files | Criteria |
|---|---|---|---|
| T1 | Tests first (red) | `tests/test_living_specs.py` | AC4, AC5 |
| T2 | `living_specs.py` (`apply`, `check`), stdlib | `skills/spec-agent/scripts/living_specs.py` | AC4 |
| T3 | Workflow: spec template section, `templates/living.md`, `state.md` layout and `living` field, `lifecycle.md` apply step, analyst reads truth, doc-writer fallback | `skills/spec-agent/**`, `agents/analyst.md`, `agents/doc-writer.md` | AC1–AC4 |
| T4 | Two sequential sandbox tickets (001, 003) run inline in a scratch copy; eval check for the area file | `evals/cases/sandbox-001.toml` (evidence in `verify.md`) | AC5 |
| T5 | Docs and release 0.3.28 (OpenSpec credit) | `docs/spec-agent.md`, roadmap, CHANGELOG, VERSION, generated manifests | AC6 |

Risk: spec-agent files load into context; keep each addition to a few lines (check `tokens`).
