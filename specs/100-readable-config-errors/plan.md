# Plan: Readable config errors

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none. New `ERROR`/`WARN` lines on bad config; valid
  config prints nothing new (AC8). New helper `config.check_config()` is internal.
- **Migrations / data changes:** none
- **Security triggers touched:** none (reads the user's own config; no writes, no secrets)
- **Domains:** scripting
- **Environments affected on deploy:** none; users get it on their next `aicfg` run
- **Destructive or replacing changes:** none

## Approach
All harness and pack config goes through `config._read_toml` and `config._layered`. Make
`_read_toml` turn `tomllib.TOMLDecodeError` into `ConfigError("<~path>:<line>: <msg>")`, taking
the line from tomllib's `(at line N, column M)` (`at end of document` → the file's last line).
Add a schema per layered name in `config.py`: `HARNESS_KEYS` / `PACK_KEYS` mapping each known key
to `bool` or `str`. `_check_toml(path, text, data, known_tables)` checks one file's raw dict
before merging, so the error names the file the value is in: a non-dict top-level value or a
wrongly typed known key raises `ConfigError`; an unknown key, or (harnesses only) a table the
base `harnesses.toml` doesn't define, is returned as a warning string. `_layered` calls it on
both files and raises on errors, so every existing caller is protected (no more `TypeError`).

Lines for values: tomllib has no positions, so `_line_of(text, table, key)` scans lines,
tracking `[table]` headers, and returns the line of `key =` inside that table; it falls back to
the table header (or the top-level `table =` line for inline tables, or 1). Good enough for
the hand-written files these are; dotted keys land on their table's line.

Warnings are printed once per command. `config.check_config() -> list[str]` runs the checks on
both names and returns the warnings (raising on errors). `cli._sync`, `validate.cmd_validate`,
and `doctor.doctor_findings` call it first: `_sync` and `cmd_validate` print `ERROR <e>` and
return 1 on `ConfigError`, else `WARN` each warning; doctor turns them into FAIL / WARN
findings (a FAIL stops doctor, as the agents_format check does today). `pack.toml` gets the same
treatment in `sources.load_pack`, reusing `_line_of` and the decode-error formatting.

Closed stdout: `cli.main` wraps the dispatch; on `BrokenPipeError` it points stdout at
`os.devnull` (so the interpreter's final flush can't raise again) and returns 0.

Design choice: validate per file before the merge instead of on the merged dict. The merged dict
has lost which file and line a value came from, which AC1-AC3 need.

## Files
| File | Change |
|---|---|
| `aicfg/config.py` | decode errors with line; key schemas; `_line_of`, `_check_toml`, `check_config` |
| `aicfg/cli.py` | `_sync` calls `check_config` first; `main` handles `BrokenPipeError` |
| `aicfg/validate.py` | `cmd_validate` calls `check_config` first |
| `aicfg/doctor.py` | `doctor_findings` turns `check_config` results into findings; drop the now-unneeded `TOMLDecodeError` catch |
| `aicfg/sources.py` | `load_pack`: decode errors with line, `name`/`prefix` must be strings |
| `tests/test_aicfg.py` | new `ConfigErrorTest(TempRepoCase)` |

## Risks
- A local harness table outside `harnesses.toml` is legitimate (spec Q1): it warns, still loads.
- Shipped `harnesses.toml` must use only known keys (AC8); the test runs validate on it.
- Packs read `[name]` tables from `packs.local.toml` with any name, so only their keys are checked.

## Test strategy
Unit tests in `tests/test_aicfg.py`, `ConfigErrorTest(TempRepoCase)`, writing bad
`harnesses.local.toml` / `packs.local.toml` / `pack.toml` into the temp repo and running
`cmd_sync(False)`, `cmd_sync(True)`, `cmd_validate`, and `doctor_findings` via `quiet()`:
assert exit 1, the `ERROR <file>:<line>:` text, no `Traceback`, and nothing written to a fake
HOME. AC7 runs `scripts/aicfg.py` as a subprocess with its stdout read end closed at once and
asserts no `Traceback` on stderr and exit 0.

## Tasks
- [ ] **T1** [agent: implementer] Errors with file and line for harness and pack config
  - files: `aicfg/config.py`, `aicfg/cli.py`, `aicfg/validate.py`, `aicfg/doctor.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3
- [ ] **T2** [agent: implementer] Warnings for unknown keys and local-only harness tables
  - files: `aicfg/config.py`, `aicfg/cli.py`, `aicfg/validate.py`, `aicfg/doctor.py`, `tests/test_aicfg.py`
  - criteria: AC4, AC5, AC8
  - after: T1
- [ ] **T3** [agent: implementer] `pack.toml` syntax and `name`/`prefix` types
  - files: `aicfg/sources.py`, `tests/test_aicfg.py`
  - criteria: AC1, AC6
  - after: T1
- [ ] **T4** [agent: implementer] Quiet exit on a closed stdout
  - files: `aicfg/cli.py`, `tests/test_aicfg.py`
  - criteria: AC7
