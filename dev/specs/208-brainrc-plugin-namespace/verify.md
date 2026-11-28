# Verify: Plugin namespace brainrc@brainrc

Run at 2026-10-28T17:03:51Z on commit `8417140`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (also with `XDG_CONFIG_HOME` set as on CI) | pass: 580 tests, OK (1 skipped: chmod test under root, covered by a mocked PermissionError test) |
| Lint | not configured | not configured |
| Build | `python3 scripts/brainrc.py plugin` re-run after commit | pass: no diff, manifests current |
| Validate (infra) | `python3 scripts/brainrc.py validate`; `--pack examples/pack-acme`; sandbox tests | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | PluginTest/CursorPluginTest pin `brainrc` names; `rg ai-config .claude-plugin .cursor-plugin plugin.json` finds nothing | pass |
| AC2 | validate OK; test: an old-name manifest is reported stale with the plugin-command fix | pass |
| AC3 | manifest names give install id `brainrc@brainrc` (live `/plugin install` out of scope, per spec) | pass |
| AC4 | tests/test_plugin_docs.py (install commands use `brainrc@brainrc`) | pass |
| AC5 | tests/test_plugin_docs.py; docs/install.md "Moving from ai-config" | pass |
| AC6 | tests/test_plugin_docs.py (SKILL.md names `brainrc:<role>` before `ai-config:<role>`) | pass |
| AC7-AC9 | tests/test_doctor_plugin.py (Cursor: old link or dir → WARN; with new too → WARN; new only or none → nothing) | pass |
| AC10 | tests/test_doctor_plugin.py (Claude Code `ai-config@ai-config` → WARN, alone or next to `brainrc@brainrc`) | pass |
| AC11 | tests/test_doctor_plugin.py (missing, invalid, unreadable, wrong shape, deeply nested, >1 MB → no finding, no exception; parent not searchable) | pass |
| AC12 | suite and validate pass offline on temp HOMEs | pass |

## Notes
- The live `/plugin install brainrc@brainrc` can't run offline; AC3 is covered by the manifest names.
