# Plan: Keep file mode and follow symlinks on every write

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none (`write_settings` and `write_mcp` keep their signatures)
- **Migrations / data changes:** none
- **Security triggers touched:** filesystem writes and permissions of a file that can hold
  secrets (`~/.claude.json`); symlink handling. T1 gets `review: each` + security review.
- **Domains:** scripting
- **Environments affected on deploy:** none; users get it on their next `aicfg apply`
- **Destructive or replacing changes:** none

## Approach
`write_settings` (`aicfg/settings.py`) and `write_mcp` (`aicfg/mcp.py`) duplicate the same
back-up, prune, tmp-write, `os.replace` sequence. Move it into one helper,
`replace_file(dest: Path, text: str)`, in `aicfg/settings.py`. `write_settings` calls it with the
JSON text; `write_mcp` imports and calls it, then records ownership as today. `mcp.py` importing
`settings.py` adds no cycle (`settings` → `plan` → `config`/`sources`/`opencode`). gh:97 then
changes temp naming and locking in this one place.

The helper resolves `dest` with `Path.resolve()` (non-strict, so a dangling link resolves to its
would-be target) and does all its work beside the **target**: backup, prune, temp file, rename.
Renaming over the target keeps the link and stays atomic because the temp file is in the
target's directory. If the target exists, its permission bits are read first
(`stat.S_IMODE`). The temp file is unlinked if a stale one is left over, then created with
`os.open(O_WRONLY|O_CREAT|O_EXCL, 0o600)` when the target exists (so the content is never
looser than `0600` before the rename), then `os.chmod`'d to the target's bits just before
`os.replace`. With no existing target it is created with `0o666`, so the umask gives today's
default (spec non-goal: new files keep their current mode).

Design choice: a helper in `settings.py` rather than a new module. Two callers, one place,
no new file; `BACKUPS_KEPT` is already imported there.

## Files
| File | Change |
|---|---|
| `aicfg/settings.py` | add `replace_file`; `write_settings` uses it |
| `aicfg/mcp.py` | `write_mcp` uses `replace_file`; drop now-unused imports |
| `tests/test_aicfg.py` | settings-file tests in `SyncFakeHomeTest`: mode, symlink, dangling link, backup beside target, temp mode before rename |
| `tests/test_mcp.py` | `McpSyncTest`: `0600` `~/.claude.json` kept, symlinked `~/.claude.json` kept |

## Risks
- A stale `.aicfg-tmp` from a crash with loose bits would keep them under `O_TRUNC`; mitigated
  by unlink + `O_EXCL`.
- `resolve()` on a symlink loop raises `RuntimeError`/`OSError`; acceptable (apply fails loudly,
  file untouched), not covered by a criterion.
- Windows: `os.chmod` only toggles read-only; the mode tests skip on Windows (`os.name == "nt"`).

## Test strategy
Unit/integration tests through `aicfg.cmd_sync` with a fake `HOME`, as the existing tests do.
AC5 patches `os.replace` in `aicfg.settings` to record the temp file's mode at rename time and
asserts it is `0600` for a `0600` target. Symlink tests assert `is_symlink()`, `readlink()`
unchanged, target content merged, backups and no `.aicfg-tmp` beside the target.

## Tasks
- [ ] **T1** [agent: implementer] `replace_file` helper; settings writes keep mode and follow links
  - files: `aicfg/settings.py`, `tests/test_aicfg.py`
  - criteria: AC2, AC3, AC5, AC6, AC7
  - review: each
- [ ] **T2** [agent: implementer] MCP writes use `replace_file`
  - files: `aicfg/mcp.py`, `tests/test_mcp.py`
  - criteria: AC1, AC4
  - after: T1
