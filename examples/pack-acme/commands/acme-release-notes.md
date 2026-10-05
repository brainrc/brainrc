---
description: Draft release notes for an Acme service from merged PRs since a tag
---

Draft release notes for $ARGUMENTS (a service name and the previous tag, e.g. `billing v1.4.0`).

1. List merged PRs since the tag with `git log --merges --oneline <tag>..HEAD`.
2. Group them as Features, Fixes, and Operations. Skip chores.
3. Link each entry to its `ACME-*` ticket if the PR names one.

Write the draft to `release-notes.md`. Don't publish or tag anything.
