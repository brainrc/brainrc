---
bump: patch
---
- `validate` checks more of a pack: relative links in its `README.md` and `docs/**`, references
  inside rules (core's too), and skills named in prose ("the acme-deploy skill") as well as
  "`acme-deploy` skill". A pack may ship its own OpenCode plugin as `overrides/opencode/plugin.js`:
  `apply` links it beside core's guard plugin (`brainrc-guard-<pack>.js`) and the lock records it
  with the pack's hooks. The example packs' READMEs link core's docs on GitHub, so a copy keeps
  working links (#137).
