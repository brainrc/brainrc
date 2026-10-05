## analyst · spec · done
2026-10-05T13:11:34Z

**Did:** Wrote spec.md from gh:7: copyable example pack, unit test + CI step, docs link.

**Evidence:**
- read docs/packs.md, validate workflow, pack test fixture

**Changed files:** `specs/007-example-pack/spec.md`

**Open issues:** 7 criteria, 4 open questions (each with a default)

**Next:** Spec gate

## architect · plan · done
2026-10-05T13:17:11Z

**Did:** Wrote plan.md: example mirrors docs/packs.md layout; ExamplePackTest reuses cmd_validate; separate CI step.

**Evidence:**
- read cmd_validate, frontmatter checks, ticket-jira config keys, validate workflow

**Changed files:** `specs/007-example-pack/plan.md`

**Open issues:** 2 tasks; callouts: CI workflow step; spec deviation (two prefixed skills, intake_context needs its own)

**Next:** Plan gate

## implementer · T1 · done
2026-10-05T13:19:38Z

**Did:** Added examples/pack-acme (pack.toml with requires_core and all four extension points, acme-deploy domain skill, acme-context intake skill, rule, command, tripwire, README) and ExamplePackTest.

**Evidence:**
- red: ExamplePackTest failed on assertion (no pack.toml)
- `validate --pack examples/pack-acme` → OK, no WARN
- AC4 mutation: VERSION 0.2.0 → ExamplePackTest fails naming requires_core (reverted)
- tripwire fires on a non-allowed line (reverted)
- full suite → 47 OK; core validate → OK; no home paths

**Changed files:** `examples/pack-acme/**`, `tests/test_aicfg.py`

**Open issues:** none

**Next:** T2
