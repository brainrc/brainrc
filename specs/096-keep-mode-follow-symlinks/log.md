# Log: 096-keep-mode-follow-symlinks

## engine · intake · done
2026-10-25T18:38:25Z

**Did:** Child 1 of campaign gh:92. Branch 096-keep-mode-follow-symlinks from main (campaign checkpoint 1ed6f5a). ticket.md from gh:96. Size standard (security trigger: writes a file that can hold secrets), mode fallback (installed agents link to a stale ~/projects/ai-config copy), domains: scripting, offline only.

**Evidence:**
- `python3 -m unittest discover -s tests` → 367 passed (baseline)
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** specs/096-keep-mode-follow-symlinks/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-25T18:39:46Z

**Did:** Wrote spec.md: 7 criteria (mode kept, symlinks followed, temp never looser, backups, dangling link), new living area aicfg-apply.

**Evidence:**
- `living_specs.py check` → would update specs/living/aicfg-apply.md

**Changed files:** specs/096-keep-mode-follow-symlinks/spec.md

**Open issues:** 1 open question (backup location for symlinked files; default beside target).

**Next:** Spec gate

## architect · plan · done
2026-10-25T18:41:53Z

**Did:** Wrote plan.md: one `replace_file` helper in settings.py used by both writers; resolve link, back up/temp/rename beside target, temp created 0600 (O_EXCL after unlinking a stale one), chmod to target bits before rename.

**Evidence:** read-only inspection of aicfg/settings.py, aicfg/mcp.py, import graph, tests.

**Changed files:** specs/096-keep-mode-follow-symlinks/plan.md

**Open issues:** none. Callout: security trigger (file perms, symlinks); T1 review: each.

**Next:** Plan gate

## implementer · T1 · done
2026-10-25T18:45:25Z

**Did:** Added `replace_file` + `_create` in settings.py; `write_settings` uses it. Resolves links, backs up and renames beside the target, temp and backup created 0600 (O_EXCL after unlink) then chmod to the target's bits. Backup no longer goes through `shutil.copy2`, which briefly left it at the umask mode.

**Evidence:**
- red: 4 new tests fail on assertions (420 != 384, [438] != [384], is_symlink False ×2)
- `python3 -m unittest discover -s tests` → 371 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** aicfg/settings.py, tests/test_aicfg.py

**Open issues:** none

**Next:** review T1

## code-reviewer · T1 · done
2026-10-25T18:45:25Z

**Did:** Reviewed T1 diff against AC2, AC3, AC5, AC6, AC7.

**Findings:**
- LOW aicfg/settings.py:_create: writes bytes, so Windows no longer gets \r\n translation and encoding is UTF-8 instead of the locale → acceptable (JSON is ASCII; UTF-8 is correct for TOML); mention in PR.
- LOW aicfg/settings.py:_create: backups no longer keep the original mtime (copy2 did) → backups sort by name, no reader uses mtime; accept.
- LOW aicfg/settings.py:replace_file: a symlink loop raises from `resolve()` → apply fails loudly, file untouched; plan risk, no criterion.

**Open issues:** none

**Next:** commit T1

## security-reviewer · T1 · done
2026-10-25T18:45:25Z

**Did:** Checked paths/symlinks and secrets handling (security-checklist: Paths, State and secrets).

**Findings:**
- LOW aicfg/settings.py:_create: `os.chmod(path)` after close instead of `fchmod(fd)` → path could be swapped between create and chmod, but only by someone who can already write the user's config dir; hardening only (fchmod is POSIX-only before 3.13).
- LOW aicfg/settings.py:replace_file: a newly created file still gets the umask default (0644 typical) → spec non-goal; follow-up to create MCP files 0600.

**Open issues:** none

**Next:** commit T1

## implementer · T2 · done
2026-10-25T18:46:32Z

**Did:** `write_mcp` calls `replace_file`; removed its duplicate sequence and the now-unused imports.

**Evidence:**
- red: 2 new tests fail on assertions (420 != 384, is_symlink False)
- `python3 -m unittest discover -s tests` → 373 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** aicfg/mcp.py, tests/test_mcp.py

**Open issues:** none

**Next:** batched review
