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

## code-reviewer · batched review · changes-requested
2026-10-27T02:25:02Z

**Did:** Reviewed `git diff main...HEAD` (aicfg, tests) against spec.md. review_context: shared.

**Evidence:**
- HIGH aicfg/config.py toml_error: end-of-document error one line early without a final newline (`[a]\npath = "x` → :1:) → count lines
- MEDIUM tests: end-of-document test hit the "Illegal character" branch → drop the final newline
- LOW validate --pack also checks the machine's harness config (accepted, AC1 scope)

**Changed files:** none

**Open issues:** none after F1

**Next:** F1

## implementer · F1 · done
2026-10-27T02:25:02Z

**Did:** `toml_error` counts lines with `splitlines()`; test now ends without a newline and asserts line 2. Re-review of the fix diff: no findings.

**Evidence:**
- red: test asserted `:2:`, got `:1:`
- `python3 -m unittest discover -s tests` → 409 passed

**Changed files:** aicfg/config.py, tests/test_aicfg.py

**Open issues:** none

**Next:** verify

## verifier · verify · done
2026-10-27T02:25:02Z

**Did:** Re-ran tests and validate on 89e3bc7, mapped AC1-AC8 to tests plus manual runs on a scratch copy.

**Evidence:**
- `python3 -m unittest discover -s tests` → 409 passed
- `python3 scripts/aicfg.py validate` → OK

**Changed files:** specs/100-readable-config-errors/verify.md

**Open issues:** none (note: apply.lock is created before the config check; pre-existing)

**Next:** document

## doc-writer · document · done
2026-10-27T02:26:23Z

**Did:** Applied the delta (new specs/living/aicfg-config.md). Added a "Config errors" table to docs/troubleshooting.md, changelog.d/100-readable-config-errors.md (patch), pr-body.md, ticket-comment.md.

**Evidence:**
- `living_specs.py apply` → updated specs/living/aicfg-config.md
- `python3 scripts/aicfg.py validate` → OK (fragment valid, plugin manifests not stale)

**Changed files:** docs/troubleshooting.md, changelog.d/100-readable-config-errors.md, specs/living/aicfg-config.md, specs/100-readable-config-errors/pr-body.md, ticket-comment.md

**Open issues:** none

**Next:** child 1 verified; child 2 gh:101
