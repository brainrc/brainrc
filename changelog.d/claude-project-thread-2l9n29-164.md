---
bump: patch
---
- `brainrc import` reads Cursor rules (`.cursor/rules/**/*.mdc` and `.cursorrules`): `alwaysApply` rules become rules in order; a rule scoped by `globs` becomes a skill with a row in Gatework's Domains table for those globs; one with only a description becomes a skill. Each keeps a comment naming its file and lines (#164).
