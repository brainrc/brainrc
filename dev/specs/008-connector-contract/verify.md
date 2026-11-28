# Verify: Ticket-connector contract, validated

Run at 2026-10-05T17:11:17Z on commit `f770e66`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests -q` | pass: 59 tests (55 before) |
| Validate (core) | `python3 scripts/aicfg.py validate` | pass |
| Validate (example) | `python3 scripts/aicfg.py validate --pack examples/pack-acme` | pass |
| Sandbox | `python3 -m unittest -q` in `examples/sandbox` | pass |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `references/connectors.md`: operations table (required, kind, allowed stage/gate, does), local-only section | pass |
| AC2 | contract Implementation section; `ticket-github` MCP equivalents table and description | pass |
| AC3 | `ConnectorCheckTest` (core and pack cases); manual: dropping `link_pr` from `ticket-local` → `ERROR skills/ticket-local/SKILL.md: connector missing \`##\` sections for link_pr` (restored) | pass |
| AC4 | core validate and example validate pass; `test_core_connectors_pass`, combined-heading test | pass |
| AC5 | `docs/spec-agent.md` Extending and spec-agent SKILL.md references link the contract (validate checks links) | pass |
| AC6 | `docs/packs.md`: one `[extensions.ticket]` per pack, with the reason | pass |
| AC7 | `## 0.3.0` tagged [pack contract], `VERSION` 0.3.0, example pin `>=0.3, <0.4` (old pin fails at 0.3.0, reverted); suite and validates pass | pass |
