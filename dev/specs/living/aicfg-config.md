# aicfg-config

How aicfg reads and checks its own config files.

### Readable config errors
`brainrc` SHALL report a TOML syntax error, a non-table top-level value, or a wrongly typed known key in `harnesses.toml`, `packs.toml`, their `.local.toml` overrides, or a pack's `pack.toml` as `ERROR <file>:<line>: <what>`, with no traceback, and exit 1 without writing. (AC1, AC2, AC3, AC6)
_Last changed by 209-brainrc-docs-wording._

### Unknown config names warn
`brainrc` SHALL warn with file and line about an unknown key in a harness or pack table and about a harness table defined only in `harnesses.local.toml`, and continue. (AC4, AC5, AC8)
_Last changed by 209-brainrc-docs-wording._

### Closed output
`brainrc` SHALL exit without a traceback when its stdout is closed early. (AC7)
_Last changed by 209-brainrc-docs-wording._

### Unique pack names
`brainrc` SHALL refuse, with an error naming both `packs.toml` keys, two enabled packs with the same name, or a pack named `core`, in `validate`, `status`, `apply`, and `doctor`, and `apply` SHALL write nothing while it stands. (AC1, AC2, AC3, AC4)
_Last changed by 209-brainrc-docs-wording._

### Apply checks packs first
`brainrc status` and `brainrc apply` SHALL run the checks `validate --pack` runs on each enabled pack's own files, and on any error SHALL print it, write nothing, and exit 1. (AC1, AC2, AC3, AC4)
_Last changed by 209-brainrc-docs-wording._

### Git packs follow their config
`brainrc apply` SHALL fetch a git pack whenever its configured `git` URL or `ref` differs from the one it last fetched (or none is recorded), `brainrc status` SHALL report that it would, and `brainrc doctor` SHALL report the mismatch. (AC1, AC2, AC3, AC4, AC5, AC7)
_Last changed by 209-brainrc-docs-wording._

### Git calls time out
`brainrc` SHALL stop any git call after 60 seconds and report it as an error. (AC6)
_Last changed by 209-brainrc-docs-wording._

### Agent model and tool names
`brainrc validate` SHALL accept an agent `model` that is `haiku`, `sonnet`, `opus`, `inherit`, or a full `claude-` model ID, and `Task` among its `tools`, and SHALL reject any other model or tool name (except `mcp__` tools). (AC1, AC2, AC3)
_Last changed by 209-brainrc-docs-wording._

### Settings home
The system SHALL resolve its settings home by the order above, defaulting to `~/.config/brainrc`,
and SHALL NOT read the legacy `~/.config/ai-config` or `AICFG_HOME`; while either holds an unmigrated
home, `status`, `apply` and `update` SHALL write nothing and exit 1 with an error naming `brainrc migrate`. (AC3, AC4, AC5)
_Last changed by 238-remove-deprecated-names._

### Migrate
`brainrc migrate` SHALL move the old home to the new one, re-run apply so no link points into the
old dir, refuse a non-empty target, support `--dry-run`, and be idempotent. (AC7 to AC13)
_Last changed by 206-brainrc-settings-home._
