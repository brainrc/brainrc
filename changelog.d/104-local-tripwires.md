---
bump: patch
---
- `validate` reads an optional, gitignored `tripwires.local.toml` (`terms = [...]`) and fails on any tracked core file whose name or text contains one of the terms, ignoring case, so each maintainer can keep employer and client names out of core without committing them. A tracked symlink is checked by the target path git commits, not by the file it points at, and binary files are skipped. It also fails if that file is ever tracked. The pre-commit hook runs it on every commit.
