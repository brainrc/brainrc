# Verify: Remove ai-config's hooks when a harness is disabled

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_disabling_harness_removes_only_its_owned_hooks`: ai-config groups gone, foreign group and `tui` key kept, backup written; `test_uninstall_restores_the_settings_file`: `{"theme": "dark"}` back exactly | pass |
| AC2 | same test: `status` prints `MERGE claude ~/.claude/settings.json`, file unchanged | pass |
| AC3 | `test_disabled_harness_without_settings_is_left_alone`: no settings file created | pass |
| AC4 | `test_hooks_left_in_a_disabled_harness`: one settings FAIL naming "claude is disabled", fix `apply`; doctor exit 0 after apply | pass |
| AC5 | Uninstall section is now 3 steps with no manual hook removal; VERSION 0.3.9, CHANGELOG 0.3.9; `validate` OK | pass |

## Real run
Fake HOME with `{"theme": "dark"}` in `~/.claude/settings.json`, `apply`, disable all five
harnesses, `apply`: settings back to `{"theme": "dark"}`, 0 links, `doctor` "No problems found."

## Changes from the spec
- The first real run left `"hooks": {}` behind. `merge_settings` now drops the `hooks` key when
  ai-config emptied it, keeping a user's own empty `{}`. Test added, red first.
- Noted: a disabled harness's settings file that isn't valid JSON is now a `CONFLICT` in
  `apply`, the same as for an enabled harness.
