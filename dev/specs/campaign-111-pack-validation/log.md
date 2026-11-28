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

## engine · gh:137 · verified
Draft PR #371 (base `main`, stacked on #370). `validate` and the full suite passed before the push.

## engine · gh:138 · Spec and Plan (logged under the Campaign gate)
- Spec: `test = "<dir or file>.py"` in `pack.toml` names the pack's unittest tests; `validate --pack`
  from the command line runs them in a fresh Python (cwd the pack's root, brainrc importable, no
  bytecode written), and fails when one fails, none is found, or the path isn't a directory or `.py`
  file in the pack. `doctor` (which passes the pack's key) and `apply` never run them, so they need
  no permission or lock entry, unlike a validator. `brainrc.testing` gives `run_hook`, `bash`,
  `assert_denies` (exit 2 counts), `assert_asks` and `assert_allows` (allow or no opinion).
- The homelab example's rule tests move from core's tests/test_hooks.py into the pack; core keeps
  the "core no longer asks" and fragment checks, and CI validates both example packs.
- Plan: `brainrc/testing.py`, `brainrc/packtests.py` (new), `brainrc/validate.py`, the pack.toml
  schema, examples/pack-homelab (tests/, pack.toml, README), docs/packs.md (Pack tests), the
  workflow; tests in `tests/test_pack_tests.py`.

## engine · gh:138 · verified
`validate --pack examples/pack-homelab` runs its 6 tests; a guard with a rule removed fails it.
`validate` and the full suite (1216 tests) passed before the push.

## engine · gh:138 · draft PR
Draft PR #372 (base `main`, stacked on #371).

## engine · gh:139 · Spec and Plan (logged under the Campaign gate)
- Spec: a composite action at `.github/actions/validate-pack/` runs `validate --pack <path>` with
  the core it is pinned to (GitHub checks out this repository at the pinned ref, so the action's
  own directory is the core). Inputs: `path`, `default-packs`, `python-version`; inputs reach the
  shell through `env` only. (Review changed how it gets the default packs: see below.) `.pre-commit-hooks.yaml` adds `brainrc-validate-pack` (`language: python`, the
  installed `brainrc`). Core's CI checks acme and homelab with the action from this checkout.
- Not done here: tagging a release that carries the action, publishing it to the Marketplace, and
  a private pack's CI adopting it. Those are the maintainer's.
- Plan: the action, `.pre-commit-hooks.yaml`, the workflow, `scripts/check_install.py` (a pack's
  tests from the installed package), docs/packs.md, the acme README; tests in
  `tests/test_validate_pack_action.py`.

## engine · gh:139 · verified
The action's two steps, run by hand with a scratch home, fetched Gatework and passed acme. The
installed-wheel smoke test passed, including `validate --pack` on homelab. `validate` and the full
suite passed before the push.

## engine · gh:139 · draft PR
Draft PR #373 (base `main`, stacked on #372).

## review · code-review (high) on each PR, fixes on its own branch, merged forward
- #369 (gh:135): 10 findings, 8 fixed. Schema findings became validate-only (apply installs a pack
  as before), a decimal budget counts, unknown keys name their table and real line, form-aware
  unknown-key collection, one error per bad `id`, `url` + `env_from = []` allowed, harness names
  free, docs on which files have schemas. Kept: the `patch` bump (apply is unaffected, only
  validate is stricter) and the per-reader type guards (refusing at load would fail every command).
- #370 (gh:136): 8 findings, 6 fixed. Connector config is validate-only and checked once;
  `metadata()` reads wrapped, quoted and block values and skips nested maps; a broken declaration
  checks no pack; the instructions tripwire follows `paths`/`exclude` and names the matching line;
  one shared line finder and hint (`config.key_line`, `config.did_you_mean`). Kept: a separate
  `metadata()` parser (changing `parse_frontmatter` touches every skill) and the `patch` bump.
- #371 (gh:137): 10 findings, 9 fixed. README/docs links, rule references and prose names are
  validate-only; prose names need the pack prefix or a head two skills share, and skip "skill set";
  `/docs/x.md` and `%20` links resolve; a relative link in a rule warns; an orphaned pack plugin
  link is removed; dotfile plugin names; harnesses.toml read once. Kept: example READMEs link
  `blob/main` (a copied pack keeps working links).
- #372 (gh:138): 9 findings, 9 fixed. `run_hook` fails on a missing or hung hook, reads JSON with no
  decision as no opinion; `assert_no_opinion`; unittest's report stays in view; a test file name
  unittest can't import is named; core's hook tests share the helper; AGENTS.md updated.
- #373 (gh:139): 8 findings, 7 fixed. New `validate --pack <dir> --fetch-defaults` fetches the
  default packs at the refs core pins into `$BRAINRC_HOME/validate-packs/`, so the action no longer
  runs `apply` in a fake home: one step, a settings home per call, setup-python only when asked.
  The pre-commit hook uses the same flag and takes the pack's directory as `args`. Kept: core's CI
  fetches Gatework again for the action (it exercises the action as pack authors run it).
