---
bump: patch
---
- `status` (and `apply`) now list rendered files that are out of date, such as `instructions.md`
  after you edit a rule: `UPDATE` when it differs from what `apply` would write, `CREATE` when
  it's missing, and `PRUNE` for an `extensions.md` or OpenCode agent copy that `apply` deletes.
  Before, `status` said "Everything in sync." until `apply`, and only `doctor` noticed an edited
  rule. `status` and `doctor` now use the same check.
