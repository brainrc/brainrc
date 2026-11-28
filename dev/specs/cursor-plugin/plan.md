# Plan: Cursor plugin and guards

Spec: approved (ask handling: A, deny both) · Mode: inline · Domains: none (Python tooling)

| Task | What | Files | Criteria |
|---|---|---|---|
| T1 | Tests first: adapter cases, Cursor merge, manifest and rule checks (red) | `tests/test_hooks.py`, `tests/test_aicfg.py` | AC1–AC4 |
| T2 | `overrides/cursor/hooks/guard.py` and `overrides/cursor/settings.fragment.json` | `overrides/cursor/**` | AC2 |
| T3 | Merge: flat `{command}` entries count as owned; a fragment's top-level keys (`version`) are set when absent; `[cursor]` hooks_dir and settings | `aicfg/settings.py`, `aicfg/plan.py`, `harnesses.toml` | AC3 |
| T4 | `.cursor-plugin/plugin.json` from `aicfg plugin`; `alwaysApply: true` in rules and validate checks it | `aicfg/plugin.py`, `aicfg/validate.py`, `rules/*.md`, generated manifests | AC1 |
| T5 | Check the manifest against Cursor's schema (scratch); baseline transcript diff | none (evidence in `verify.md`) | AC3, AC4 |
| T6 | Docs and release 0.3.26 | README, `docs/*.md`, CHANGELOG, VERSION | AC5 |

Risks: Cursor may reject rule `.md` files or our agents' `model` values (unverifiable here,
documented). Claude Code must not pick up the Cursor hooks: they live in `.cursor-plugin/plugin.json`
inline and in `overrides/cursor/`, not in a root `hooks/hooks.json`.
