---
bump: patch
---
- Project scope (#282): in a repo with a `brainrc.toml`, `apply` also writes the repo's own agent
  files: its packs' skills, copied to `.agents/skills/`, and their rules, in a marked block in
  `AGENTS.md` that leaves your own text alone. Default packs (Gatework) are on unless
  `brainrc.toml` turns them off, and it can pin them or add packs by `git` or by a `path` in the
  repo. `status` shows the user scope and then the project. `brainrc.lock` records the files brainrc
  wrote, so a file it didn't write is reported as a conflict and left alone. Nothing machine-local
  reaches the project. Without a `brainrc.toml`, nothing changes.
