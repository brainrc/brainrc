---
bump: patch
---
- New `brainrc uninstall` takes out everything `apply` put into the harnesses: the links it made (broken ones too), its hooks in each settings file, and the MCP servers it added, then the files and directories that leaves empty. Your own settings, hooks and servers stay, rewritten files are backed up first, and an instructions file `brainrc init` moved aside is put back. It works after the checkout or a pack is moved or deleted, using the harnesses and source roots `apply` recorded in `$BRAINRC_HOME/harnesses.json`. `--dry-run` shows what goes; `--purge` also deletes `$BRAINRC_HOME` with your local config and fetched git packs. docs/troubleshooting.md's Uninstall section now uses it.
