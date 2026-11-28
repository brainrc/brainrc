# Plan: aicfg reports these problems instead of crashing

No new dependency or public API change.

## Approach
- `sources._markdown_under`: list only real files (a dangling link is reported by validate's
  existing symlink check).
- `plan.invalid_fragments(srcs) -> list[str]`: `<src.rel(file)>: invalid JSON (<error>)` for each
  fragment that doesn't parse. `cmd_sync` stops on it before writing (like collisions); doctor
  adds each as a FAIL and skips settings checks that would render a bad fragment.
- `plan.render_fragment` raises `FragmentError(ConfigError)` on bad JSON, so `plugin` prints
  `ERROR` (its existing ConfigError path) and `check_plugin` stays quiet (validate already
  reports the file once).
- `doctor_findings`: check each harness's `agents_format` before planning; an unknown one is a
  FAIL finding and the link checks that need it are skipped.
- `settings.merge_settings`: iterate existing events, then the fragment's new ones, in order.

## Tasks
| id | title | agent | files | criteria |
|---|---|---|---|---|
| T1 | tests first, one per case | implementer | tests/test_aicfg.py | AC1–AC4 |
| T2 | fixes | implementer | aicfg/{sources,plan,cli,doctor,plugin,settings}.py | AC1–AC4 |
| T3 | before/after output diff, docs and release | implementer | CHANGELOG.md, VERSION | AC5 |
