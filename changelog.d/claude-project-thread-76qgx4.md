---
bump: patch
---
- The default pack is now Gatework v0.8.0, which no longer installs the old spec-agent names
  (`spec-agent`, `kubernetes`, `analyst` and the rest). The next `apply` removes their links; use
  the `brainrc-` names. A pack that still names an old one in `[extensions.gatework]` gets a warning
  until Gatework 0.9.0.
