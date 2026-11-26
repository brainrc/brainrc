---
bump: patch
---
- A git pack can come from one folder of a repo: `subdir = "python"` next to `git` and `ref`, so one
  repo (brainrc/packs) holds many packs. The lock records the folder (lock version 3 when one is
  set), and `install --frozen` and `check` honour it (#121).
- An item `exclude` leaves out no longer collides, so an official pack can take over a skill a
  default pack still ships while that pack's copy is excluded (#318).
- `brainrc/python`, `brainrc/node-ts` and `brainrc/rust` are official pack IDs, and the official
  table in docs/packs.md links each pack's folder in brainrc/packs (#183, #184, #185).
