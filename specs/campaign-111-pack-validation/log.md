# Campaign gh:111 · validation for pack authors (E9)

## 2026-11-16T02:20:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:111 --shape ordered --dry-run`

- Members, in order: #135 (published JSON Schemas), #136 (connector config schema), #137
  (validate covers more), #138 (pack tests and a guard-test harness), #139 (validate-pack Action
  and pre-commit hook). All open, none assigned, none skipped.
- Shape: `ordered` (given, and the epic body names it). Dependency source: `none` (no links
  between the children; the order is the epic's: schemas, then the checks that use them, then the
  Action that runs them all).
- Delivery: `stacked` (the epic body), carried as one draft PR per child against `main`, each
  branch stacked on the previous one (as in E12, E26, E27 and E28). Merge in order, merging `main`
  into the next branch first.
- The epic's "start after #93 (E2), #95 (D1)" is an ordering note, not a dependency: E2's children
  are all closed; D1's open items are owner decisions that this campaign doesn't touch.
- Old issue bodies name `aicfg/`; the package is `brainrc/`. Schemas go in `docs/schemas/` beside
  E27's `brainrc.toml` and `brainrc.lock` schemas, checked by the same stdlib validator
  (`brainrc/schema.py`), not a second `schemas/` folder.
- Ticket connectors (`brainrc-ticket-*`) and `references/connectors.md` now live in
  brainrc/gatework, which this campaign doesn't change: #136 builds the core side (a skill declares
  its config, `validate` checks a pack's table against it) and the Gatework side is a follow-up there.
- Publishing the Action to the Marketplace, or tagging it, stays with the maintainer.

## engine · Campaign gate · approved
The coordinator's brief (passing on the maintainer's "start the next epic", run like E12 and E26)
says to dry-run, then build the children in order as draft PRs, each sent to review. Recorded as
approved on that basis; per-child Spec and Plan gates are logged here rather than stopped on.
Merging stays with the maintainer.

## engine · gh:135 · Spec and Plan (logged under the Campaign gate)
- Spec: JSON Schemas (draft 2020-12) for `pack.toml`, `mcp/servers.toml` and `harnesses.toml` in
  `docs/schemas/`, each key described for completion. `.taplo.toml` maps a checkout's files to them;
  a pack elsewhere names its schema on a `#:schema` first line, which the import writer
  (`brainrc/scaffold.py`) and the example packs now carry. `validate` checks a pack's `pack.toml`
  against its schema with the stdlib validator: a known key of the wrong type fails (before, a string
  `max_always_tokens` crashed the budget check), and an unknown key warns, naming the closest known
  key. `mcp/servers.toml` and `harnesses.toml` keep their existing hand-written checks (which already
  refuse or warn on unknown keys); a test pins each schema's keys to the ones the code reads.
  `extensions` stays open: each namespace is checked by the pack that owns it, and the legacy
  top-level forms still load.
- Plan: `docs/schemas/*.schema.json`, `brainrc/schema.py` (`minimum`, unknown keys collected),
  `brainrc/validate.py` (`pack_toml_findings`), `brainrc/scaffold.py`, `brainrc/tokens.py`,
  `brainrc/plugins.py`, `brainrc/naming.py` (wrong types no longer crash), `.taplo.toml`, docs;
  tests in `tests/test_pack_schemas.py`.
