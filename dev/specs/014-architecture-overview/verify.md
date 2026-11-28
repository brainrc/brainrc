# Verify: Architecture overview with one diagram

Run at 2026-10-05T18:08:44Z on commit `028f017`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 59 tests |
| Validate | `python3 scripts/aicfg.py validate` (incl. CHANGELOG/VERSION) | pass |
| Links | relative file links and 5 heading anchors checked by script | all resolve |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | Mermaid flowchart: sources → aicfg apply → per-harness dirs → spec-agent reads extensions.md → agents, domain skills, connector | pass |
| AC2 | "Install time vs run time" table with reads/writes per step | pass |
| AC3 | Glossary: harness, core, pack, skill, domain skill, agent, connector, gate, requires_core, each linked | pass |
| AC4 | README line under the intro; VERSION 0.3.2; CHANGELOG entry; validate and tests pass | pass |
| AC5 | 54 lines; all links resolve | pass |

## Notes
- Mermaid rendering itself is confirmed on the PR page after push.
