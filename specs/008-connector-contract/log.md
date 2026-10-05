## analyst · spec · done
2026-10-05T17:04:29Z

**Did:** Wrote spec.md from gh:8: contract doc, connector heading check in validate, one-per-pack decision, 0.3.0.

**Evidence:**
- read the three connector skills' headings and the pack ticket extension validation

**Changed files:** `specs/008-connector-contract/spec.md`

**Open issues:** 7 criteria, 3 open questions with defaults

**Next:** Spec gate

## architect · plan · done
2026-10-05T17:07:15Z

**Did:** Wrote plan.md: check_connectors (heading word match, one heading may cover several ops), contract doc, MCP table in ticket-github, links, 0.3.0.

**Evidence:**
- read cmd_validate, pack ticket extension validation, ticket-github commands

**Changed files:** `specs/008-connector-contract/plan.md`

**Open issues:** 4 tasks; callout: 0.3.0 contract change

**Next:** Plan gate

## test-writer · T1 · done
2026-10-05T17:09:04Z

**Did:** ConnectorCheckTest: core connectors pass (guard), core ticket-x missing link_pr fails, combined heading passes (guard), pack connector named in [extensions.ticket] missing three ops fails under validate --pack.

**Evidence:**
- `python3 -m unittest tests.test_aicfg.ConnectorCheckTest` → 2 failures (assertions on missing behavior), 2 guards pass

**Changed files:** `tests/test_aicfg.py`

**Open issues:** none

**Next:** review T1

## code-reviewer · T1 · done
2026-10-05T17:09:04Z

**Did:** Reviewed T1 against AC3, AC4.

**Evidence:**
- pack fixture cleaned up via addCleanup; core version pinned via set_core_version

**Changed files:** none

**Findings:** none

**Open issues:** none

**Next:** commit T1, then T2

## implementer · T2 · done
2026-10-05T17:09:34Z

**Did:** check_connectors(srcs): core ticket-* plus pack [extensions.ticket].connector (resolved across sources); whole-word match of each required op in the skill's ## headings; wired into cmd_validate.

**Evidence:**
- ConnectorCheckTest OK; suite 59 OK; validate OK; example OK

**Changed files:** `scripts/aicfg.py`

**Open issues:** none

**Next:** review T2

## code-reviewer · T2 · done
2026-10-05T17:09:34Z

**Did:** Reviewed T2 against AC3, AC4.

**Evidence:**
- unknown connector names are skipped here (already reported by _validate_pack); \b handles link_pr

**Changed files:** none

**Findings:**
- LOW scripts/aicfg.py check_connectors: a "## fetch" line inside a code fence counts as a heading → follow-up; the check is documented as shallow.

**Open issues:** none

**Next:** commit T2, then T3

## implementer · T3 · done
2026-10-05T17:10:13Z

**Did:** New references/connectors.md (operations table, local-only delivery, CLI or MCP, shallow-check note); spec-agent SKILL.md links it; ticket-github gains an MCP equivalents table and its description names the MCP server; docs/spec-agent.md Extending links the contract.

**Evidence:**
- suite OK; validate OK (links resolve); spec-agent refs +~500 tokens on use, always-loaded +~5

**Changed files:** `skills/spec-agent/references/connectors.md`, `skills/spec-agent/SKILL.md`, `skills/ticket-github/SKILL.md`, `docs/spec-agent.md`

**Open issues:** none

**Next:** T4
