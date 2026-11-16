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

## engine · gh:135 · verified
Draft PR #369 (base `main`). `validate` and the full suite passed before the push. Taplo itself
couldn't be installed in the build environment, so the editor association is checked by tests
(schema paths exist; the `#:schema` URL names the file on `main`), not in an editor.

## engine · gh:136 · Spec and Plan (logged under the Campaign gate)
- Spec: a connector skill declares its config in SKILL.md frontmatter under the Agent Skills
  `metadata` map (so spec-following harnesses load it unchanged), as
  `brainrc-config: "key: type [required]; ..."` with types string, integer, boolean, list.
  `validate` (and `apply`, through the pack checks) finds every `[extensions.<ns>.<table>]` or
  legacy `[extensions.<table>]` with a `connector`, and checks it against that skill's declaration:
  a wrong type or a missing required key fails, an undeclared key warns (`notes` names its
  replacement). `connector` and `instructions` are allowed in every such table; `instructions` is the
  defined field for free-form guidance, and the pack's tripwires check it with a `pack.toml` line.
  A bad declaration fails on the skill. A connector that declares nothing isn't checked.
- `blocked_status` and declarations on the real `brainrc-ticket-*` skills, plus
  `references/connectors.md`, live in brainrc/gatework: a follow-up there. Core's stand-in fixture
  declares the Jira connector's config, and the acme example sets `blocked_status` and `instructions`.
- Plan: `brainrc/connectors.py` (new), `brainrc/validate.py`, the fixture's Jira skill,
  `examples/pack-acme/pack.toml`, docs/packs.md (Connector config), docs/formats.md; tests in
  `tests/test_connector_config.py`.

## engine · gh:136 · verified
Draft PR #370 (base `main`, stacked on #369). `validate` and the full suite passed before the push.

## engine · gh:137 · Spec and Plan (logged under the Campaign gate)
- Spec: `validate` runs its reference check (relative links, `[agent: x]`, "`x` skill") over every
  source's rules and a pack's `README.md` and `docs/**`, and also catches a skill named in prose,
  "the x skill", when x is hyphenated and starts like a known skill or the pack's prefix (so "the
  follow-up skill" stays prose). A pack's `overrides/<harness>/plugin.js` is linked for a harness
  with `plugin` set, as a sibling of core's file (`brainrc-guard-<pack>.js`), removed with the pack,
  and recorded in the lock as one of the pack's hooks; a plugin for a harness that loads none fails.
  The example READMEs link core's docs by URL, since a pack copied out of this repo broke them.
- Plan: `brainrc/validate.py`, `brainrc/plan.py`, `brainrc/config.py` (`pack_plugin_path`),
  `brainrc/permissions.py`, examples, docs/packs.md, docs/guardrails.md; fixture
  `tests/fixtures/pack-prose-refs/`; tests in `tests/test_validate_coverage.py`.
