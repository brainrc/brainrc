---
bump: patch
---
- `apply` fetches a git pack again when its `ref` or `git` URL changes, and `status` shows the `FETCH` line first. Before, a pack was fetched only when its clone was missing, so bumping `ref` did nothing. The fetched URL and ref are recorded in the clone's `.git/aicfg-fetched.json`, and clones from older versions are fetched once. `doctor` reports a clone that doesn't match its config. Git calls stop after 60 seconds instead of hanging `apply` (gh:103).
