---
bump: patch
---
- Bad config in `harnesses.toml`, `packs.toml`, their `.local.toml` overrides, or a pack's `pack.toml` now prints `ERROR <file>:<line>: <what>` and exits 1 before anything is written. Before, a syntax error showed a traceback, `claude = false` raised `TypeError`, and `enabled = "false"` counted as enabled. Unknown keys and harness tables only the local file defines (`[cursr]`) print a `WARN` with file and line instead of being ignored (gh:100).
- `aicfg doctor | head` and other early-closed pipes exit quietly instead of printing a `BrokenPipeError` traceback.
