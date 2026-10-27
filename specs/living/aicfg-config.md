# aicfg-config

How aicfg reads and checks its own config files.

### Readable config errors
aicfg SHALL report a TOML syntax error, a non-table top-level value, or a wrongly typed known key
in `harnesses.toml`, `packs.toml`, their `.local.toml` overrides, or a pack's `pack.toml` as
`ERROR <file>:<line>: <what>`, with no traceback, and exit 1 without writing. (AC1, AC2, AC3, AC6)
_Last changed by 100-readable-config-errors._

### Unknown config names warn
aicfg SHALL warn with file and line about an unknown key in a harness or pack table and about a
harness table defined only in `harnesses.local.toml`, and continue. (AC4, AC5, AC8)
_Last changed by 100-readable-config-errors._

### Closed output
aicfg SHALL exit without a traceback when its stdout is closed early. (AC7)
_Last changed by 100-readable-config-errors._
