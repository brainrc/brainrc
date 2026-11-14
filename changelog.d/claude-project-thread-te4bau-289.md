---
bump: patch
---
- Permission diff (#289): `brainrc.lock` now records what each pack can do: the hooks it adds, its
  MCP servers, its tool grants (agents' `tools`, skills' `allowed-tools`, settings it sets) and the
  network domains those name. `status` prints `PERMS <pack> + <kind> <entry>` for what apply would
  add and `-` for what it would remove. `apply`, `update` and `install` ask before adding any, and
  `--yes` accepts them; without a terminal to ask in and without `--yes` they refuse and write
  nothing. A machine's first lock lists them once and records them as the baseline; a lock from
  before this release counts as the baseline while the pack's files are unchanged. `check` fails
  when a lock's permission record doesn't match its packs. The lock spec gains
  `[packs.<key>.permissions]` (additive; schema and fixtures updated).
