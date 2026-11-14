---
bump: minor
---
- Permission diff (#289): `brainrc.lock` now records what each pack can do: the hooks it adds, its
  MCP servers, its tool grants (agents' `tools`, skills' `allowed-tools`, settings it sets) and the
  network domains those name. `status` prints `PERMS <pack> + <kind> <entry>` for what apply would
  add and `-` for what it would remove. `apply`, `update` and `install` ask before adding any, and
  `--yes` accepts them; without a terminal to ask in and without `--yes` they refuse and write
  nothing. A machine's first lock lists them once and records them as the baseline; a lock from
  before this release counts as the baseline while the pack's files are unchanged. `check` fails
  when a lock's permission record doesn't match its packs. The lock spec gains
  `[packs.<key>.permissions]` and goes to version 2: brainrc reads versions 1 and 2 and writes 2, so
  brainrc 0.7.6 and older refuse a new lock with "upgrade brainrc" instead of a schema error.
