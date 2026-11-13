---
bump: patch
---
- Tests run on Windows: a shared `tests/support.py` deletes read-only git files at cleanup, sets
  `USERPROFILE` beside `HOME` for a fake home (Windows reads only `USERPROFILE`), and child
  processes keep `SYSTEMROOT`. Temp dirs are resolved (no 8.3 short names) and pack paths are
  written as TOML literal strings, so a Windows path's backslashes aren't read as escapes (#342).
- Windows: links to a skill or hooks directory are made as directory links (a file link to a
  directory reads as broken there), link targets drop the `\\?\` prefix Windows adds, a hooks dir
  is written into hook commands with `/` and JSON-escaped, and messages show paths with `/`
  (`~/.claude/skills/...`, `rules/10-git.md`), so `exclude` patterns and tripwire `paths` match
  on every OS (#342).
- Windows: `brainrc doctor | head` exits quietly there too (a closed pipe raises `EINVAL` on
  flush), `init` and `uninstall` move a file aside over a same-second backup as they do on
  macOS and Linux, and `scripts/check_tutorial.py` runs Git Bash from `PATH` instead of the WSL
  launcher Windows finds first (#342).
