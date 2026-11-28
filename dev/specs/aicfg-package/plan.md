# Plan: aicfg becomes a package

No new dependency. Public surface unchanged: `python3 scripts/aicfg.py <command>`, same output.
Adds `aicfg/` at the repo root and `python3 -m aicfg`.

## Modules (import order, no cycles; from a dependency scan of the current sections)
| module | from today's sections |
|---|---|
| `config` | header constants + config: `REPO`, TOML layering, harnesses, `$AICFG_HOME` and render paths, `ConfigError` (spec listed `paths` separately; they share every caller, so one module) |
| `sources` | sources, rule and extension renders, plus `frontmatter` and `_markdown_under` (moved down from validation: sources needs them, and leaving them would make a cycle) |
| `opencode` | `agents_format`, `opencode_agent`, `rendered_agents` and their constants |
| `plan` | planning: `Link`, `SettingsMerge`, `plan`, stale links |
| `settings` | Claude settings merge |
| `plugin` | Claude and Antigravity manifests |
| `tokens` | token estimates and budgets, `cmd_tokens` |
| `validate` | validation, `cmd_validate` |
| `doctor` | doctor |
| `cli` | `cmd_sync`, `main`, and the usage text (`main` prints it) |

## How
- A throwaway script splits `scripts/aicfg.py` by its top-level statements (each keeps the
  comments above it), writes each module with only the imports it uses, and rewrites bare
  `REPO` to `config.REPO` (via the AST, so strings are untouched): tests patch one place.
- `aicfg/__init__.py` re-exports the names tests and `scripts/evals.py` use; `aicfg/__main__.py`
  runs `cli.main`. `scripts/aicfg.py` becomes a shim that puts the repo root on `sys.path`.
- Tests: import the package; `aicfg.REPO` → `aicfg.config.REPO`, the budget patch →
  `aicfg.tokens.CORE_ALWAYS_BUDGET`. `scripts/evals.py` imports the package.

## Tasks
| id | title | agent | files | criteria |
|---|---|---|---|---|
| T1 | split into the package; shim, `__init__`, `__main__` | implementer | aicfg/*, scripts/aicfg.py | AC1–AC3 |
| T2 | tests and evals import the package | implementer | tests/test_aicfg.py, scripts/evals.py | AC4 |
| T3 | before/after output diff in a fixed fake HOME | implementer | none | AC5 |
| T4 | docs and release | implementer | AGENTS.md, CONTRIBUTING.md, docs/architecture.md, VERSION, CHANGELOG.md | AC6 |
