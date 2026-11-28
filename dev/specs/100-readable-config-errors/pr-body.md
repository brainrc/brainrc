Report bad config with file and line

1 of 5 in epic #93 (E2: Config and pack loading).

## Why
A mistake in `harnesses.toml`, `packs.toml`, their `.local.toml` overrides, or a pack's `pack.toml` gave a Python traceback for a syntax error and a `TypeError` for `claude = false`. A wrong type was silently accepted: `enabled = "false"` counted as enabled. Typos like `[cursr]` or `enabeld = false` were ignored, so config the user meant to turn off stayed on. `aicfg doctor | head` crashed with `BrokenPipeError`.

## What changed
- `aicfg/config.py` checks each file before `.local.toml` is merged over the shipped one, so an error names the file the value is in. Syntax errors, non-table top-level values, and wrongly typed known keys (`LAYERED_KEYS`: `enabled` is a boolean, paths and `ref` are strings) raise `<file>:<line>: <what>`. tomllib gives a line only for syntax errors, so `line_of` scans for the key inside its `[table]`.
- Unknown keys, and harness tables only the local file defines, come back as warnings. A locally added harness still loads.
- `check_config()` runs first in `status`/`apply`, `validate`, and `doctor`. They print `ERROR` and exit 1 before writing, or print each `WARN` once. `doctor` reports them as FAIL or WARN.
- `load_pack` reports `pack.toml` syntax errors and a non-string `name` or `prefix` the same way.
- `main` flushes stdout inside a `BrokenPipeError` handler and exits 0.
- `docs/troubleshooting.md` gets a "Config errors" table. New living area `specs/living/aicfg-config.md`.

## Acceptance criteria
- [x] AC1: syntax errors name file and line and exit 1, verified by `test_toml_syntax_error_names_file_and_line`, `test_toml_syntax_error_at_end_of_document`, `test_syntax_error_in_shipped_file`, `test_pack_toml_syntax_error_names_file_and_line`
- [x] AC2: `claude = false` asks for a table, verified by `test_top_level_value_needs_a_table`
- [x] AC3: non-boolean `enabled` and non-string paths fail, verified by `test_enabled_must_be_a_boolean`, `test_pack_enabled_must_be_a_boolean`, `test_path_keys_must_be_strings`, `test_inline_table_value_points_at_its_line`
- [x] AC4: unknown keys warn, verified by `test_unknown_harness_key_warns`, `test_unknown_pack_key_warns`
- [x] AC5: a harness only in the local file warns and still loads, verified by `test_harness_only_in_local_file_warns_and_still_loads`
- [x] AC6: `pack.toml` `name`/`prefix` must be strings, verified by `test_pack_name_and_prefix_must_be_strings`
- [x] AC7: a closed stdout exits 0 with no traceback, verified by `ClosedStdoutTest`
- [x] AC8: the shipped config prints no new WARN or ERROR, verified by `test_shipped_config_is_quiet`

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
printf '[codex]\nenabled = "false"\n' > harnesses.local.toml && python3 scripts/aicfg.py status; rm harnesses.local.toml
```

## Follow-ups
- `apply` still takes `$AICFG_HOME/apply.lock` before reading config, so a config error leaves that lock file (no harness file is written).
- `validate --pack DIR` also checks the machine's own harness and pack config.
- Value lines come from a line scan: a dotted key (`claude.enabled = …`) is reported at its `[table]` header, or line 1 when there is none.

Spec: `specs/100-readable-config-errors/spec.md` · Plan: `specs/100-readable-config-errors/plan.md`
Closes #100
