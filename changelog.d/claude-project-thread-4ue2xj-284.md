---
bump: patch
---
- `brainrc install --frozen` (#284) installs exactly what `brainrc.lock` records: each git pack at
  its locked commit, never its ref, and every file checked against its hash before anything is
  written. Any mismatch (a pack only in the config or the lock, another URL, ref or path, a commit
  that can't be fetched, a file that differs) is named, nothing is written and it exits 1. It
  defaults to the project when there is a `brainrc.toml`, else the user scope; `--scope` picks one.
