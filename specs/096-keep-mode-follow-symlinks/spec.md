# Spec: Keep file mode and follow symlinks on every write

Ticket: gh:96 · Size: standard · Status: approved

## Problem
`aicfg apply` rewrites harness settings files (`settings.json`, hooks) and MCP config files
(`~/.claude.json` and others) by writing a temp file and renaming it over the target. The temp
file gets the default mode from the umask, so a `0600` `~/.claude.json`, which can hold MCP
tokens, comes back `0644` and readable by other local users. When the target is a symlink (a
dotfiles-managed `settings.json`), the rename replaces the link with a plain file, so the merged
hooks never reach the dotfiles target and the user's link is silently broken.

## Goals
- An existing file's permission bits survive every settings and MCP write.
- A symlinked settings or MCP file stays a symlink, and its target receives the new content.
- A write never exposes the content with looser permissions than the file had, even briefly.

## Non-goals
- Locking concurrent applies and pid-unique temp names (gh:97).
- Ownership (uid/gid) preservation: aicfg runs as the file's owner.
- Changing the mode of files aicfg creates fresh (no existing file): they keep today's default.
- In-place `write_text` writers (rendered instructions, extensions, plugin files, the owned-servers
  record): writing in place already keeps mode and follows links.

## Acceptance criteria
- **AC1**: Given an MCP config file with mode `0600`, when `aicfg apply` merges servers into it,
  then the file's mode is still `0600` afterwards.
- **AC2**: Given a harness settings file with a non-default mode (e.g. `0600` or `0640`), when
  `aicfg apply` merges hooks into it, then its mode is unchanged afterwards.
- **AC3**: Given a settings file that is a symlink to a file elsewhere (a dotfiles target), when
  `aicfg apply` merges hooks, then the path is still a symlink to the same target, and the target
  holds the merged hooks.
- **AC4**: Given an MCP config file that is a symlink, when `aicfg apply` merges servers, then the
  path is still a symlink to the same target, the target holds the merged servers, and the
  target's mode is unchanged.
- **AC5**: Given a `0600` target, when the new content is written to the temp file, then the
  temp file's mode is never more permissive than `0600` at any point before the rename.
- **AC6**: Given a symlinked target, when a write happens, then the timestamped backup holds the
  target's previous content and sits beside the target, and no temp file is left behind.
- **AC7**: Given a symlink whose target does not exist yet (dangling link), when `aicfg apply`
  writes that file, then the target is created with the content and the link is kept.

## Constraints
- Stdlib only (AGENTS.md). Works on macOS and Linux; Windows behavior must not regress.
- Writes stay atomic: a crash never leaves a half-written target.
- Security trigger: filesystem writes of a file that can hold secrets. Needs security review.

## Requirement changes

### Area: aicfg-apply
Purpose: How `aicfg apply` writes harness settings and MCP config files.
#### ADDED: Safe atomic writes
`aicfg apply` SHALL write settings and MCP files atomically, keep an existing file's permission
bits, and never expose the new content with looser permissions than the file had. (AC1, AC2, AC5)
#### ADDED: Symlinked config files
When a settings or MCP file path is a symlink, `aicfg apply` SHALL write through to the link's
final target (creating it if the link dangles), keep the link, and back up the target's previous
content. (AC3, AC4, AC6, AC7)

## Open questions
None. Q1 resolved at the Spec gate: backups of a symlinked file sit beside the target (AC6).
