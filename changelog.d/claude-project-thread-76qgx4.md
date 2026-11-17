---
bump: patch
---
- `status` (and `apply`) now list a rendered file that is out of date, such as `instructions.md`
  after you edit a rule, as `UPDATE ... (rules or packs changed since the last apply)`, and a
  missing one as `CREATE`. Before, `status` said "Everything in sync." until `apply`, and only
  `doctor` noticed. Both use the same check.
