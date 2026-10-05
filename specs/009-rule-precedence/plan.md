# Plan: Explicit rule precedence across core, packs, and local rules

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** rendered rule order for packs (breaking under the version
  policy) → `0.2.0`; `validate` gains a CHANGELOG/VERSION check that every future PR must satisfy.
- **Migrations / data changes:** none. Users re-run `apply` to re-render.
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** each machine's rendered instructions file, on next `apply`
- **Destructive or replacing changes:** none

## Approach
Rewrite `render_instructions` (`scripts/aicfg.py`) to walk `srcs` in order instead of merging
everyone's files into one sorted list. Core's `markdown_files("rules", src)` render first,
unlabelled, so a core-only render is byte-identical to today (AC4). Each pack with rules gets
`<!-- pack: <name> -->` plus one line, `Rules from pack <name>. They refine the rules above and
never override them.`, then its rules in filename order. `*.local.md` from all sources render
last under `<!-- local -->` and `Machine-local rules. They refine the rules above and never
override them.`, sorted as today. The label is a comment plus a sentence, not a heading, so the
rules' own `#` headings keep their structure. The sentence is for the model, the comment is for
humans and tools.

New `_check_changelog()` beside `core_version()`: reads `CHANGELOG.md`, errors on an
`## Unreleased` heading (case-insensitive) and when the first `## X.Y.Z` heading differs from
`VERSION`. `cmd_validate` calls it with the existing `core_version()` block, so it also runs
under `validate --pack` (core is always validated).

Tests: `copy_repo` also copies `CHANGELOG.md`. A helper `set_core_version(repo, v)` writes
`VERSION` and a one-heading `CHANGELOG.md`, replacing the bare `VERSION` writes, so pack tests
keep passing under the new check.

## Files
| File | Change |
|---|---|
| `scripts/aicfg.py` | modify: `render_instructions`, `_check_changelog`, wire into `cmd_validate` |
| `tests/test_aicfg.py` | modify: render-order tests, changelog tests, `copy_repo`, `set_core_version` |
| `docs/packs.md` | modify: layout line, order + refine policy, example pin `>=0.2, <0.3` |
| `docs/formats.md` | modify: Rules section states the order and policy |
| `examples/pack-acme/pack.toml` | modify: `requires_core = ">=0.2, <0.3"` |
| `VERSION`, `CHANGELOG.md` | `0.2.0`, tagged entry |

## Risks
- Branch conflicts with #30 (also bumps `VERSION`/CHANGELOG to 0.1.2), mitigated by merging
  main after #30 lands. This PR's entry stays `0.2.0`.
- Existing pack users see pack rules move, mitigated by the [pack contract] entry and the bump.

## Test strategy
Unit tests on `render_instructions` with a fixture pack whose rule is `15-acme.md`: order, label,
local last, core-only identical (compare against the old algorithm's output on core alone).
`_check_changelog`: match passes, mismatch fails naming both, Unreleased fails.

## Tasks
- [ ] **T1** [agent: test-writer] Contract tests for render order and labels
  - files: `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC4
  - review: each
- [ ] **T2** [agent: implementer] New `render_instructions`
  - files: `scripts/aicfg.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC4
  - review: each
- [ ] **T3** [agent: implementer] `_check_changelog` in validate, with tests
  - files: `scripts/aicfg.py`, `tests/test_aicfg.py`
  - criteria: AC7
- [ ] **T4** [agent: implementer] Docs, example pin, 0.2.0 release
  - files: `docs/packs.md`, `docs/formats.md`, `examples/pack-acme/pack.toml`, `VERSION`, `CHANGELOG.md`
  - criteria: AC5, AC6, AC8
