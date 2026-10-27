# Log: 100-readable-config-errors

## engine · intake · done
2026-10-27T02:10:27Z

**Did:** Child 1 of campaign gh:93. Branch 100-readable-config-errors from main (campaign checkpoint 7bbb87b). ticket.md from gh:100. Size standard (4+ files: config, sources, doctor, cli, tests; real design choice on error locations), mode fallback (role agents not installed in this session), domains: scripting, offline only.

**Evidence:**
- `python3 -m unittest discover -s tests` → 394 passed (baseline)
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** specs/100-readable-config-errors/ticket.md, state.json

**Open issues:** none

**Next:** analyst · spec

## analyst · spec · done
2026-10-27T02:11:31Z

**Did:** Wrote spec.md: 8 criteria (syntax errors with line, non-table values, wrong types, unknown keys and harness tables warn, pack.toml name/prefix, closed stdout, no noise on shipped config), new living area aicfg-config.

**Evidence:**
- `living_specs.py check` → would update specs/living/aicfg-config.md

**Changed files:** specs/100-readable-config-errors/spec.md

**Open issues:** 2 open questions (local-only harness table: keep or skip; exit code on closed stdout).

**Next:** Spec gate

## engine · Spec gate approved
2026-10-27T02:11:54Z

- Open questions 1 and 2 resolved with their defaults (keep loading local-only harness tables; exit 0 on closed stdout). Spec change after approval (wording only): marked both resolved.

## architect · plan · done
2026-10-27T02:13:21Z

**Did:** Wrote plan.md: 4 tasks (config errors with line; unknown-name warnings; pack.toml; closed stdout). Per-file checks before the layered merge, `check_config()` called once by status/apply, validate, doctor.

**Evidence:**
- Read config.py, sources.py, cli.py, validate.py, doctor.py, packs.py, tests/test_aicfg.py (TempRepoCase)

**Changed files:** specs/100-readable-config-errors/plan.md

**Open issues:** none. Callouts: none.

**Next:** Plan gate

## engine · Plan gate approved
2026-10-27T02:14:02Z

## implementer · T1 · done
2026-10-27T02:15:59Z

**Did:** Per-file checks in `_layered` before the merge: decode errors with line, non-table values, wrongly typed known keys (`LAYERED_KEYS`), `line_of` scanner; `check_config()` called first by `_sync`, `cmd_validate`, `doctor_findings`. Dropped doctor's now-unneeded TOMLDecodeError catch.

**Evidence:**
- red: 8 new `ConfigErrorTest` tests failed (tracebacks, TypeError, exit 0 for `enabled = "false"`)
- `python3 -m unittest discover -s tests` → 402 passed

**Changed files:** aicfg/config.py, aicfg/cli.py, aicfg/validate.py, aicfg/doctor.py, tests/test_aicfg.py

**Open issues:** none

**Next:** T2

## implementer · T2 · done
2026-10-27T02:17:36Z

**Did:** `_check_toml` returns warnings for unknown keys and (harnesses) tables only the local file defines; `check_config()` collects them; `_sync` and `cmd_validate` print `WARN`, doctor adds WARN findings.

**Evidence:**
- red: 3 new warning tests failed on assertions (no WARN line)
- `python3 -m unittest discover -s tests` → 406 passed; `validate` OK, `status` 0 WARN lines

**Changed files:** aicfg/config.py, aicfg/cli.py, aicfg/validate.py, aicfg/doctor.py, tests/test_aicfg.py

**Open issues:** none

**Next:** T3

## implementer · T3 · done
2026-10-27T02:18:53Z

**Did:** `load_pack` formats pack.toml decode errors with `toml_error` and rejects non-string `name`/`prefix` with their line.

**Evidence:**
- red: syntax test errored with a TOMLDecodeError traceback; type test failed (exit 0)
- `python3 -m unittest discover -s tests` → 408 passed

**Changed files:** aicfg/sources.py, tests/test_aicfg.py

**Open issues:** none

**Next:** T4

## implementer · T4 · done
2026-10-27T02:20:08Z

**Did:** `main` wraps dispatch, flushes stdout inside the try, and on BrokenPipeError dups /dev/null onto stdout and returns 0.

**Evidence:**
- red: subprocess test saw a BrokenPipeError traceback from doctor
- `python3 -m unittest discover -s tests` → 409 passed

**Changed files:** aicfg/cli.py, tests/test_aicfg.py

**Open issues:** none

**Next:** batched review
