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

### Unique pack names
aicfg SHALL refuse, with an error naming both `packs.toml` keys, two enabled packs with the same
name, or a pack named `core`, in `validate`, `status`, `apply`, and `doctor`, and `apply` SHALL
write nothing while it stands. (AC1, AC2, AC3, AC4)
_Last changed by 101-reject-duplicate-pack-names._

### Apply checks packs first
`aicfg status` and `aicfg apply` SHALL run the checks `validate --pack` runs on each enabled
pack's own files, and on any error SHALL print it, write nothing, and exit 1. (AC1, AC2, AC3, AC4)
_Last changed by 102-apply-validates-packs._

### Git packs follow their config
`aicfg apply` SHALL fetch a git pack whenever its configured `git` URL or `ref` differs from the
one it last fetched (or none is recorded), `aicfg status` SHALL report that it would, and
`aicfg doctor` SHALL report the mismatch. (AC1, AC2, AC3, AC4, AC5, AC7)
_Last changed by 103-refetch-git-pack-on-change._

### Git calls time out
aicfg SHALL stop any git call after 60 seconds and report it as an error. (AC6)
_Last changed by 103-refetch-git-pack-on-change._

### Agent model and tool names
`aicfg validate` SHALL accept an agent `model` that is `haiku`, `sonnet`, `opus`, `inherit`, or
a full `claude-` model ID, and `Task` among its `tools`, and SHALL reject any other model or
tool name (except `mcp__` tools). (AC1, AC2, AC3)
_Last changed by 202-validate-model-ids-task-tool._

### Settings home
The system SHALL resolve its settings home by the order above, defaulting to `~/.config/brainrc`,
use a legacy `~/.config/ai-config` or `AICFG_HOME` only as a fallback with a once-per-run stderr
warning, and never prefer the old dir when the new one exists. (AC1 to AC6)
_Last changed by 206-brainrc-settings-home._

### Migrate
`brainrc migrate` SHALL move the old home to the new one, re-run apply so no link points into the
old dir, refuse a non-empty target, support `--dry-run`, and be idempotent. (AC7 to AC13)
_Last changed by 206-brainrc-settings-home._
