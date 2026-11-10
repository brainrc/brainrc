---
bump: patch
---
- `apply --repair` fixes the links a moved checkout leaves broken, or a package upgrade to a new Python: each broken link that points at the same item's old location (`skills/<name>`, `agents/<name>.md`, ...) is relinked, and links into the old location whose item is gone are pruned. Old locations come from `$BRAINRC_HOME/harnesses.json` and from the broken links themselves, so installs from before the manifest repair too; a location inferred from a broken link is only pruned when it no longer exists, so your own working links stay. `status --repair` shows the changes first. Without `--repair`, `apply` says how many of its conflicts it could repair, and `doctor` suggests `apply --repair` for them. A broken link to anything else stays a `CONFLICT`.
