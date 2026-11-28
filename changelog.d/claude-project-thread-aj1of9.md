---
bump: patch
---
- Windows without symlinks works end to end (#179, #120). Where git checks a pack out with
  `core.symlinks` off, each of the pack's links arrives as a plain file holding its target; copy mode
  now copies what that file points to (a chain of them too, or an item that is one), and validate
  reads a Markdown link through it. Gatework is pinned to v0.9.1, which accepts its `roles/`
  stand-in where brainrc copies it.
- `link_mode = "auto"` on Windows now also copies where git doesn't make links (`core.symlinks` off,
  Git for Windows' default), even with Developer Mode on. macOS and Linux are unchanged.
- The Windows CI cells now block, and every cell applies, checks and uninstalls in copy mode with
  symlinks off (`scripts/check_apply.py --copy`). `docs/install.md` lists Windows as supported.
