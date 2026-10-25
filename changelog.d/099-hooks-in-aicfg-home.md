---
bump: patch
---
- An installed `aicfg` copies core's guard hooks to `$AICFG_HOME/hooks/core/` and links them from there, so they keep working when `uv tool upgrade` or `pipx upgrade` moves the tool to a new Python. `status` reports a copy that no longer matches the package, and the next `apply` refreshes it. Checkouts still link hooks live.
