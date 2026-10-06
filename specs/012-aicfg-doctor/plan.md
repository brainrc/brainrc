# Plan: `aicfg doctor`

Inline mode, tests first per task. One reviewer pass over the whole diff before Verify.

| Task | What | Files | Criteria | Red test |
|---|---|---|---|---|
| T1 | Python 3.11 import guard around `tomllib` (one-line message, exit 1) | `scripts/aicfg.py`, `tests/test_aicfg.py` | AC7 | run `aicfg.py` with a stub that hides `tomllib` (`python3 -c` with `sys.modules["tomllib"] = None`) and assert the message, not a traceback |
| T2 | `cmd_doctor()` + `doctor` in `main()`: render, packs, per-harness home/links/settings; `Finding` lines with `fix:`; exit code | `scripts/aicfg.py`, `tests/test_aicfg.py` | AC1–AC6, AC8 | `DoctorTest` (fake HOME, temp repo): clean after apply; writes nothing; stale render; missing link; wrong link; stale link; broken link (repo moved); real-file conflict; harness not installed → WARN, exit 0; missing pack path; incompatible pack; unmerged hooks; invalid settings JSON |
| T3 | Docs and release | module docstring, `README.md`, `VERSION` 0.3.7, `CHANGELOG.md` | AC9 | `validate` (CHANGELOG/VERSION check) |

## Shape of T2
- `doctor_findings() -> list[tuple[str, str, str]]` (level, what, fix), so tests can assert
  on structure; `cmd_doctor()` prints and sets the exit code.
- Packs: walk `_layered("packs")` directly so one broken pack doesn't hide the rest; good
  packs go into the source list, so render/link checks use what `apply` would use.
- Harness home = parent of `instructions`, else of `skills`. Missing → WARN and skip.
- Links from `plan()`: map `Link.state()` to findings; a `conflict` whose dest is a symlink
  with a missing target is reported as broken (delete, then `apply`).
- `validate --pack` reused by calling `cmd_validate(path)` with stdout captured.

## Risks
- Harness home rule picks `~/.config/opencode` from `~/.config/opencode/AGENTS.md`: correct.
  Cursor has only `skills` → `~/.cursor`: correct.
