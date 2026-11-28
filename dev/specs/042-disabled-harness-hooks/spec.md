# Spec: Remove ai-config's hooks when a harness is disabled

Ticket: gh:42 · Size: small (aicfg.py ~15 lines, tests, one doc section) · Status: draft

## Problem
Disabling a harness removes its links, including the hooks directory, but leaves the hook
entries `apply` merged into its settings file. They then run a script that doesn't exist.

## Goals
- Disabling a harness and running `apply` leaves its settings file as it would be without
  ai-config: owned hook groups gone, everything else untouched.

## Non-goals
- Removing other keys from settings files (ai-config only ever merges `hooks`).

## Acceptance criteria
- **AC1**: Given a disabled harness whose settings file holds ai-config's hook groups and
  another tool's, when `apply` runs, then only ai-config's groups are removed, the other tool's
  groups and every other key stay, and a backup is written first.
- **AC2**: `status` (dry run) lists that settings file as `MERGE` and writes nothing.
- **AC3**: A disabled harness with no settings file, or one without ai-config's hooks, is left
  alone: nothing is created or backed up.
- **AC4**: `doctor` reports the leftover hooks as a FAIL ("… has ai-config's hooks but <harness>
  is disabled", fix `apply`), and nothing after that `apply`.
- **AC5**: `docs/troubleshooting.md` Uninstall drops the manual step; VERSION 0.3.9 with a
  CHANGELOG entry.

## Design
`plan()` adds a `SettingsMerge` with no fragments for each disabled harness that has a
`settings` key, with the core and pack hooks dirs as ownership markers. Merging an empty
fragment already removes owned groups and keeps the rest (`merge_settings`), and
`settings_change` already reports `ok` when nothing changes, so AC3 needs no special case.

## Open questions
None.
