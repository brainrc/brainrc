---
bump: patch
---
- Git packs are pinned to a commit (#288): once `brainrc.lock` records the commit a pack's `ref`
  resolved to, `apply`, `status` and `install` keep the pack there, on every machine, even when its
  tag is moved or its branch (or the remote's default branch) moves on. A clone found at another
  commit is put back. `brainrc update [<pack> ...]` is the one way to move a pin: it refetches the
  named packs (all when none is named, the project's too), prints the commits between the old and
  new pin and the installed files added, changed or removed, then applies and relocks. Changing
  `git` or `ref` still moves the pack on the next `apply`.
