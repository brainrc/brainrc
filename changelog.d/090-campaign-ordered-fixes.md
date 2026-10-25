---
bump: patch
---
- Ordered campaigns: the Deliver gate picks `sequential` or `stacked` delivery, and a retarget rule makes every child PR merge with base `main` (gh:77's stacked PRs merged into their stacked bases). Adds member status `verified`, a single home for `campaign.json`, and a `stacked` mode for the `campaign` eval check.
- spec-agent: `worktree_fence.py` checks a wave task's changed paths against its `files` and the main tree before landing, and status checks use `git -C <worktree>`. The architect puts a task that links to another task's new file in a later wave. `SKILL.md` says when the engine may edit an approved artifact itself.
