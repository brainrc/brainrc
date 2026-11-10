# Spec: brainrc uninstall

Ticket: gh:128 · Size: standard · Status: approved

## Problem
Removing brainrc meant disabling every harness and pack by hand, running `apply`, then deleting
the repo. Once the checkout is gone that no longer works: the links point nowhere, `apply` can't
run, and brainrc's hooks and MCP servers stay in the user's settings files.

## Goals
- One command that takes out everything apply put into the harnesses, and nothing of the user's.
- It works after the checkout (or a pack) has been moved or deleted.
- Optionally delete the settings home too.

## Non-goals
- Removing the brainrc package itself (`uv tool uninstall` does that).
- Removing brainrc's Claude Code or Cursor plugin installs (#130 covers the overlap).

## Acceptance criteria
- **AC1**: Given a HOME with the user's own settings, hooks and MCP servers, when the user runs `apply`, edits a settings file, then runs `uninstall`, then every harness config matches its pre-apply state plus that edit (brainrc's backups aside).
- **AC2**: Given links into a checkout that has been deleted, when the user runs `uninstall`, then every brainrc link is removed, found through the source roots in `$BRAINRC_HOME/harnesses.json`. A broken harnesses file falls back to the paths recorded there, with a WARN.
- **AC3**: A settings or MCP file left holding nothing of the user's is set aside as a backup; one that still holds the user's content is rewritten with a backup first. A file it can't parse is left alone and reported, and the command exits 1.
- **AC4**: Directories the removals leave empty are removed, never a harness's own home directory. Rendered files in the settings home go; local config and fetched packs stay.
- **AC5**: `--purge` also deletes the settings home; `--dry-run` prints every step and changes nothing.
- **AC6**: An instructions file `init` moved aside is put back where brainrc's link was.
- **AC7**: Run with nothing installed, or a second time, it says there is nothing to uninstall and writes nothing; `apply` afterwards reinstalls.

## Requirement changes
### Area: aicfg-apply
#### ADDED: Uninstall
`brainrc uninstall` SHALL remove every link whose target is a path brainrc links to under any source root recorded in the manifest or configured now, the hook groups and MCP servers brainrc owns, and the files and directories that leaves empty (never a harness home), SHALL back up every file it rewrites, SHALL restore an instructions file `init` moved aside, SHALL keep local config and packs unless `--purge`, SHALL refuse `--purge` when the settings home is ~, holds ~ or a harness home, or holds a file brainrc didn't make, SHALL ignore manifest entries with a path outside ~, a `hooks_dir` that holds the harness home, or a root that is ~ or holds it, and SHALL change nothing with `--dry-run`. (AC1, AC2, AC3, AC4, AC5, AC6, AC7)

## Open questions
None. Defaults taken under `--oneshot`:
1. No confirmation prompt: uninstall touches only what brainrc made, `--dry-run` shows it first, and every rewritten file is backed up.
2. A file left empty is renamed to a `*.bak-brainrc-*` backup rather than deleted outright, so nothing of the user's can be lost.
3. Without `--purge`, generated files in the settings home (rendered instructions and agents, the hooks copy, the manifest) are removed, and the user's local config stays.
