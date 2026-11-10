---
bump: patch
---
- `brainrc doctor` quotes the paths in the `rm`, `validate --pack` and `python3 <hook>` commands it suggests, keeping `~` outside the quotes so the shell still expands it, so a path with a space or quote can be pasted as is. A path beside the home directory (`/home/joe` next to `/home/jo`) is no longer shortened to a wrong `~` path.
- Docs: the install guide no longer pins v0.3.29 for staying on a release, a test fails on any install doc that pins a release other than the current major.minor, `overrides/README.md` says which harnesses are synced (Claude Code, Cursor, OpenCode), and AGENTS.md and the README say to treat the repo as public.
