---
bump: patch
---
- Tests run on Windows: a shared `tests/support.py` deletes read-only git files at cleanup, sets
  `USERPROFILE` beside `HOME` for a fake home (Windows reads only `USERPROFILE`), and child
  processes keep `SYSTEMROOT`. Temp dirs are resolved (no 8.3 short names) and pack paths are
  written as TOML literal strings, so a Windows path's backslashes aren't read as escapes (#342).
