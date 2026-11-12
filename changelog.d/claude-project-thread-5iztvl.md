---
bump: patch
---
- Gatework moves to its own repository, [brainrc/gatework](https://github.com/brainrc/gatework),
  with its history (#338). Core no longer ships `packs/gatework`: `packs.toml` names Gatework by
  `git` and a release tag, so the first `apply` fetches it and `update` refetches it. With no
  network on that first `apply`, set `enabled = false` under `[gatework]` in `packs.local.toml`, or
  `path` to a clone. Its skills, agents and names are unchanged.
- **[pack contract]** "Bundled" packs become default packs: any table in core's `packs.toml`. A
  default pack's validator plugin is trusted, and a local `path` or `git` replaces its shipped
  origin (a local `ref` alone keeps the URL). The `bundled` key is gone; `validate` warns about it.
- `validate --pack` checks a pack against core and the default packs on disk, and warns when a
  default pack isn't fetched yet.
- The plugins split: `brainrc` carries the guard hooks and rules, and Gatework is its own plugin
  (`/plugin install gatework@gatework`, roles `gatework:<role>`). Install both for what the
  `brainrc` plugin used to hold (docs/install.md, Plugins).
