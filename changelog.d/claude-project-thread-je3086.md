---
bump: patch
---
- **[pack contract]** `[scope]` in `pack.toml` says where a pack applies: globs for a git remote,
  the directory, the kube context, the AWS profile or a ticket ref, any one of which is enough.
  `brainrc scope` lists which enabled packs apply where you are and why, and `brainrc scope
  --extensions` prints the extensions a run there should read, so a work pack's deliver checks stay
  out of a personal repo. `extensions.md` ends with where each scoped pack applies. A pack without
  `[scope]` applies everywhere, as before (#140).
- **[pack contract]** `[[guard.deny]]` and `[[guard.ask]]` in `pack.toml` add rules to core's
  Claude Code guard without a hook of their own: `match` a command (its program, then words in
  order, each a glob) or `tool` an MCP tool glob, with a `reason` and an optional `scope` in place
  of the pack's. `apply` renders them into `$BRAINRC_HOME/guard-rules.json` and `guard_outward.py`
  checks them inside `sh -c`, `eval`, `$(…)` and backticks too; a pack's deny wins over any ask.
  The acme example denies `acme-deploy prod` only inside acme repos. The other tools' guards read
  the file in E11 (#141).
