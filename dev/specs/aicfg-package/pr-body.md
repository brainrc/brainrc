## Summary
`scripts/aicfg.py` (1,282 lines) is now the `aicfg/` package at the repo root. There is **no behavior change**. This prepares per-harness adapters and an installable aicfg (#50, steps 5–6).

| module | what |
|---|---|
| `config` | `REPO`, render paths, TOML layering, harnesses, constants |
| `sources` | sources and packs, rule and extension renders, `frontmatter` |
| `opencode` | OpenCode agent renders |
| `plan` | links, stale links, settings merges to do |
| `settings` | Claude settings merge |
| `plugin` | Claude and Antigravity manifests |
| `tokens` | context estimates and budgets |
| `validate` / `doctor` | as before |
| `cli` | `apply`/`status`, `main`, usage |

- **Moved by script, not rewritten.** Each top-level statement moved with the comments above it, and each module imports only what it uses. Bare `REPO` became `config.REPO` through the AST, so strings were untouched and tests patch it in one place. The dependency scan found no cycles once `frontmatter` moved down into `sources`.
- **`python3 scripts/aicfg.py <command>` still works.** It's now a shim, so README, docs, CI, pre-commit and installed users need no change. `python3 -m aicfg` works too.
- **Tests and `scripts/evals.py` import the package.** In the tests only the import and two patch targets changed (`aicfg.config.REPO`, `aicfg.tokens.CORE_ALWAYS_BUDGET`); no assertion changed.
- `VERSION` 0.3.20 (PATCH).

## Acceptance criteria
- [x] AC1 package with 10 modules, stdlib only
- [x] AC2 shim and `python3 -m aicfg`
- [x] AC3 moved, not rewritten; `config.REPO` read at call time
- [x] AC4 tests change only imports and patch targets
- [x] AC5 identical behavior, diffed for real
- [x] AC6 docs, VERSION, CHANGELOG

## Testing
- **Same output before and after.** In the same fake home directory I ran `status`, `apply` (twice), `doctor`, `tokens`, `plugin`, `validate` (core and pack) and the usage text, and captured the resulting file tree, the rendered files' hashes and the merged `settings.json`. The 600 lines are byte-identical to 0.3.19.
- `python3 -m unittest discover -s tests -q` → OK (138). The old-Python test caught a missing `import sys` in `config.py`, which is fixed.
- `validate` (core and pack), `claude plugin validate .` and `run-tutorial.sh` → OK.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
