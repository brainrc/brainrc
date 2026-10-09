# Verify: aicfg-package

| Criterion | Result | Evidence |
|---|---|---|
| AC1 package `aicfg/`, 10 modules, stdlib | pass | split by script; a scan shows every top-level name from the old file in exactly one module; no import cycles |
| AC2 `scripts/aicfg.py` and `python3 -m aicfg` | pass | shim runs every command; `-m aicfg validate` and `tokens` match the shim |
| AC3 moved, not rewritten; `config.REPO` at call time | pass | AST rewrite of bare `REPO` only; tests that patch `aicfg.config.REPO` pass |
| AC4 tests change only imports and patch targets | pass | test diff: import block + `aicfg.config.REPO` / `aicfg.tokens.CORE_ALWAYS_BUDGET`; 138 OK; validates and tutorial OK |
| AC5 identical behavior | pass | status, apply ×2, doctor, tokens, plugin, validate (core, pack), usage, the fake-HOME file tree, render hashes and settings: 600 lines, `diff` empty vs 0.3.19 |
| AC6 docs, VERSION 0.3.20, CHANGELOG | pass | AGENTS.md, README layout, docs/architecture.md |

The old-Python test caught one split bug (`config.py` missing `import sys` for the 3.11 message); fixed before commit.
