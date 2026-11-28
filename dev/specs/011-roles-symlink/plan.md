# Plan: Supported platforms and a guarded roles symlink

Inline mode, tests first.

| Task | What | Files | Criteria | Red test |
|---|---|---|---|---|
| T1 | `check_roles_link()` → error string or None; called from `validate` (core) and `doctor` | `scripts/aicfg.py`, `tests/test_aicfg.py` | AC2, AC3, AC5 | temp repo copy: `roles` replaced by a plain file containing `../../agents` → validate fails naming Platforms; link to `../../skills` → fails; real repo passes; doctor reports it |
| T2 | README Platforms section; `docs/formats.md` note; VERSION 0.3.12; CHANGELOG | `README.md`, `docs/formats.md`, `VERSION`, `CHANGELOG.md` | AC1, AC4, AC5 | `validate` |
