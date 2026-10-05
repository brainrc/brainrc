# Plan: Ticket-connector contract, validated

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** connector skills must have headings for `fetch`,
  `comment`, `transition`, `link_pr` (breaking for pack connectors without them) → `0.3.0`
- **Migrations / data changes:** none
- **Security triggers touched:** none (docs name which operations are outward and gated)
- **Domains:** scripting
- **Environments affected on deploy:** none; `validate`/`apply` on machines with pack connectors
- **Destructive or replacing changes:** none

## Approach
New `check_connectors(srcs)` in `scripts/aicfg.py`, called from `cmd_validate` after
`_validate_source`. Connectors are core skills named `ticket-*` plus every skill a pack names in
`[extensions.ticket].connector` (resolved across all sources, since a pack may reuse a core
connector). For each, collect `## ` headings from its SKILL.md and require a whole-word match for
each of `REQUIRED_CONNECTOR_OPS = ("fetch", "comment", "transition", "link_pr")` in at least one
heading, so `## comment / transition / link_pr` counts for three. The error names the skill, the
missing operations, and the contract path. Reuses `skills(src)` and the existing heading-free
`frontmatter` reader style; no new parsing helpers beyond one regex.

`skills/spec-agent/references/connectors.md` is the contract: a table of operations (required,
read-only or outward, allowed stage and gate, returns/writes), a local-only delivery section,
and one paragraph saying a connector may use a CLI or an MCP server. `ticket-github` gains an
"MCP equivalents" table next to its `gh` commands. spec-agent's SKILL.md references list and
`docs/spec-agent.md` Extending link it. `docs/packs.md` states the one-connector-per-pack limit.

## Files
| File | Change |
|---|---|
| `scripts/aicfg.py` | modify: `REQUIRED_CONNECTOR_OPS`, `check_connectors`, call in `cmd_validate` |
| `tests/test_aicfg.py` | modify: `ConnectorCheckTest` |
| `skills/spec-agent/references/connectors.md` | new: the contract |
| `skills/spec-agent/SKILL.md` | modify: add connectors to the references list |
| `skills/ticket-github/SKILL.md` | modify: MCP equivalents table |
| `docs/spec-agent.md` | modify: Extending links the contract |
| `docs/packs.md` | modify: one connector per pack, example pin |
| `examples/pack-acme/pack.toml`, `VERSION`, `CHANGELOG.md` | 0.3.0 pin and release |

## Risks
- Heading check is shallow (a heading that names an operation but says nothing still passes),
  accepted: behaviour belongs to #6. Documented in the contract.
- Context cost: connectors.md loads only on demand. Keep under ~40 lines.

## Test strategy
`ConnectorCheckTest`: core connectors pass (real repo); a core `ticket-x` missing `link_pr`
fails naming it; a combined heading passes; a pack connector named in `[extensions.ticket]`
missing sections fails under `validate --pack`.

## Tasks
- [ ] **T1** [agent: test-writer] Contract tests for the connector check
  - files: `tests/test_aicfg.py`
  - criteria: AC3, AC4
  - review: each
- [ ] **T2** [agent: implementer] `check_connectors` in validate
  - files: `scripts/aicfg.py`, `tests/test_aicfg.py`
  - criteria: AC3, AC4
  - review: each
- [ ] **T3** [agent: implementer] Contract doc, MCP equivalents, links
  - files: `skills/spec-agent/references/connectors.md`, `skills/spec-agent/SKILL.md`,
    `skills/ticket-github/SKILL.md`, `docs/spec-agent.md`
  - criteria: AC1, AC2, AC5
- [ ] **T4** [agent: implementer] One-per-pack doc, example pin, 0.3.0 release
  - files: `docs/packs.md`, `examples/pack-acme/pack.toml`, `VERSION`, `CHANGELOG.md`
  - criteria: AC6, AC7
