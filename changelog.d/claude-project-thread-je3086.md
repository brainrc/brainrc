---
bump: patch
---
- **[pack contract]** `[scope]` in `pack.toml` says where a pack applies: globs for a git remote,
  the directory, the kube context, the AWS profile or a ticket ref, any one of which is enough.
  `brainrc scope` lists which enabled packs apply where you are and why, and `brainrc scope
  --extensions` prints the extensions a run there should read, so a work pack's deliver checks stay
  out of a personal repo. `extensions.md` ends with where each scoped pack applies. A pack without
  `[scope]` applies everywhere, as before (#140).
