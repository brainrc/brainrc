# Spec: Supported platforms and a guarded roles symlink

Ticket: gh:11 · Size: standard (decision; ~4 files, ~40 lines) · Status: draft

## Decision (choose at this gate)
**Recommended: option 1, plus a guard.** Keep the symlink, state the supported platforms, and
make a broken checkout fail loudly.

- `aicfg` installs everything by symlink (skills, agents, commands, rules, hooks). Rendering
  `roles/` alone (option 2) wouldn't make Windows without symlinks work; it would add 9
  copied files and a sync check for no new platform.
- Option 3 resolves `../../agents` lexically from the harness's skills folder, e.g.
  `~/.codex/agents`, which doesn't exist for most harnesses. It breaks more than it fixes.
- Packaging that copies (the plugin issue, #26) can dereference the link at build time
  (`cp -RL`); that belongs to #26.

## Acceptance criteria
- **AC1** README has a "Platforms" section: macOS and Linux supported; Windows through WSL, or
  native with Developer Mode and `git config core.symlinks true` before cloning; why
  (everything installs by symlink).
- **AC2** `validate` fails when `skills/spec-agent/roles` isn't a symlink to `../../agents`,
  with a message that names the likely cause (checked out without symlink support) and points
  to the Platforms section.
- **AC3** `doctor` reports the same problem with the same fix.
- **AC4** `docs/formats.md` notes that `roles/` is a symlink to `agents/` and must stay one.
- **AC5** Tests: `validate` fails on a plain-file `roles` (what git writes without symlink
  support) and on a link to the wrong place; passes on the real repo. VERSION 0.3.12, CHANGELOG.

## Open questions
1. Option 1 + guard (recommended), or option 2 (render `roles/` at apply)?
