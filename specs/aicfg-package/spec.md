# Spec: aicfg becomes a package, with no behavior change

Ticket: local (prep for gh:50 steps 5–6) · Size: standard (mechanical move, 1,282 lines) · Status: approved

## Why
`scripts/aicfg.py` is one 1,282-line file. Each new harness (Cursor, guard adapters) and step 6
(installable `aicfg`, packs without a clone) adds to it. A package with one module per concern
keeps each piece reviewable and can later be installed with `pipx`/`uvx`.

## Acceptance criteria
- **AC1** The code moves to a package `aicfg/` at the repo root (open choice below), split along
  the existing section markers: `paths` (REPO, `$AICFG_HOME`, render paths), `config`
  (TOML layering, harnesses, constants, ConfigError), `sources` (sources, packs, rule and
  extension renders), `opencode` (agent render), `plan` (links, stale), `settings` (Claude
  settings merge), `validate`, `doctor`, `plugin` (Claude and Antigravity manifests), `tokens`,
  `cli` (commands, argument parsing, `main`). Still stdlib-only, Python 3.11+.
- **AC2** `python3 scripts/aicfg.py <command>` keeps working for every command (a thin shim), so
  README, docs, CI, and installed users need no change. `python3 -m aicfg` works too.
- **AC3** Code is moved, not rewritten: same functions, names, and output. Modules read shared
  state (`paths.REPO`) at call time, so tests can still point aicfg at a temp repo.
- **AC4** Tests change only to import the package and patch the module that owns a value
  (`aicfg.paths.REPO`, the budget constant); assertions don't change. `scripts/evals.py` imports
  the package. All 138 tests, both validates, and the tutorial script pass.
- **AC5** Same behavior, checked for real: `apply`, `doctor`, `tokens`, `plugin`, and `validate`
  outputs are identical before and after, in a fake HOME (diff of the outputs).
- **AC6** AGENTS.md, CONTRIBUTING.md and `docs/architecture.md` name the package; VERSION 0.3.20
  (PATCH: no behavior change); CHANGELOG.

## Not in this step
New behavior, renamed commands, packaging metadata (`pyproject.toml`), and guard adapters.

## Open choice
**Where the package lives:** (A, recommended) `aicfg/` at the repo root: `python3 -m aicfg` works
from a checkout and `pyproject.toml` can add it in step 6 without a move. (B) `scripts/aicfg_lib/`:
keeps the root unchanged, but would move again for step 6.
