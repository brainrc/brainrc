---
bump: patch
---
- **[pack contract]** Connector config schema: a connector skill declares the keys and types its
  table takes in SKILL.md frontmatter (`metadata.brainrc-config`), and `validate` checks every pack
  table that names it as `connector`: a wrong type or a missing required key fails, an undeclared
  key warns. Only `validate` reports these; `apply` still installs the pack. `instructions` is a
  defined field every connector table may set, in place of free-form `notes`, and the pack's
  tripwires check it (#136).
