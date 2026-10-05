Define the ticket connector contract, check it in validate, release 0.3.0

## Why
spec-agent reads and updates tickets only through connector skills, but which operations a connector must have, which ones reach outside systems, and which gate allows each lived only in the existing skills. A pack author had to reverse-engineer them and found a missing operation only when a run failed at Deliver.

## What changed
- **[pack contract]** `skills/spec-agent/references/connectors.md` defines `fetch`, `list`, `claim`, `comment`, `transition`, and `link_pr`: required or not, read-only or outward, allowed stage and gate, and what each writes. It also covers local-only delivery and CLI vs MCP implementations.
- `validate` fails when a connector (a core `ticket-*` skill or a pack's `[extensions.ticket].connector`) has no `##` heading for `fetch`, `comment`, `transition`, or `link_pr`. One heading may cover several.
- `ticket-github` lists the GitHub MCP tool for each `gh` command and uses them when `gh` isn't available.
- `docs/packs.md` documents one ticket connector per pack. spec-agent's SKILL.md and `docs/spec-agent.md` link the contract.
- `VERSION` 0.3.0. The example pack and the docs pin `">=0.3, <0.4"`.

Blast radius: machines with packs. Packs pinned `<0.3` fail `validate` and block `apply` until they update `requires_core`. A pack connector missing a required heading fails `validate`. Core connectors already pass.

## Acceptance criteria
- [x] AC1: contract doc with every operation
- [x] AC2: CLI or MCP, `ticket-github` MCP table
- [x] AC3: missing operation fails `validate`, verified by `ConnectorCheckTest` and a manual break of `ticket-local`
- [x] AC4: core connectors and the example pack pass
- [x] AC5: contract linked from spec-agent docs
- [x] AC6: one connector per pack documented
- [x] AC7: 0.3.0, tagged entry, example pin updated

## How to verify
```
python3 -m unittest discover -s tests -q
python3 scripts/aicfg.py validate
python3 scripts/aicfg.py validate --pack examples/pack-acme
```

## Follow-ups
- LOW: a `## fetch` line inside a code fence counts as a heading. The check is documented as shallow; behaviour tests belong to #6.

Spec: `specs/008-connector-contract/spec.md` · Plan: `specs/008-connector-contract/plan.md`
Closes #8

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
