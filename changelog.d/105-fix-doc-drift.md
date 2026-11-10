---
bump: patch
---
- `brainrc doctor` quotes the paths in the `rm`, `validate --pack` and `python3 <hook>` commands it suggests, keeping `~` outside the quotes so the shell still expands it, so a path with a space or quote can be pasted as is. A directory beside the home directory (a sibling whose name starts with the same letters) is no longer shortened to a wrong `~` path.
- `brainrc doctor` no longer suggests `rm -r` for an unused old settings home (such as `AICFG_HOME`) that contains the home directory, the settings home or the brainrc checkout. It says to move what you need and keep the directory instead.
- Docs: the install guide no longer pins v0.3.29 for staying on a release, a test fails on any install doc that pins a release other than the current major.minor, `overrides/README.md` says which harnesses are synced (Claude Code, Cursor, OpenCode), and AGENTS.md and the README say to treat the repo as public.
