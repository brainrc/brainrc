---
bump: patch
---
- `apply` writes `brainrc.lock` (#283): in the settings home for the user scope, and next to
  `brainrc.toml` for a project. For each pack it records where it came from, the commit a git
  pack's `ref` resolved to, and the SHA-256 of every file it installed, so a changed pack file
  changes its hash. A second `apply` with no change to any source leaves the lock byte-identical.
  A tag or branch that moved to another commit shows as `MOVED`, in `status` too once the clone
  has it. Credentials in a git URL never reach the lock.
