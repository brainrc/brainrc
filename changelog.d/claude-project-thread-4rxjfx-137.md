---
bump: patch
---
- **[pack contract]** `validate` checks more of a pack: relative links in its `README.md` and
  `docs/**` (a `/docs/x.md` link is read from the pack's root, as GitHub does), references inside
  rules (core's too; a relative link in a rule warns, since rules are rendered elsewhere), and
  skills named in prose ("the acme-deploy skill") as well as "`acme-deploy` skill". Only
  `validate` reports these; `apply` still installs the pack. A pack may ship its own OpenCode
  plugin as `overrides/opencode/plugin.js`: `apply` links it beside core's guard plugin
  (`brainrc-guard-<pack>.js`), removes the link with the pack (its entry deleted, too), and the
  lock records it with the pack's hooks. The example packs' READMEs link core's docs on GitHub,
  so a copy keeps working links (#137).
