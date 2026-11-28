# Plan: brainrc init

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** additive: new `init` command; new local files `rules/adopted-<harness>[-<n>].local.md`.
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** init moves the user's instructions file aside (`os.rename` to `<file>.bak-brainrc-<time>`); nothing is deleted, and a link's target is never touched.

## Approach
New `brainrc/init.py` with `cmd_init(yes, harnesses, adopt, dry_run)`. It lists every enabled
harness with whether it is installed (#126's `load_harnesses` views), chooses (a question per
installed harness, `--yes` for all of them, or `--harness` for exactly those) and edits
harnesses.local.toml line by line with `set_enabled`, so comments and other keys stay. A
`tomllib.loads` of the result guards the edit. Adoption finds each chosen harness's
`instructions` path that is a real file or a link `plan._managed_target` doesn't recognise,
which is exactly what apply would call a CONFLICT. It writes the text, with a header comment,
to `rules/adopted-<harness>.local.md` in `config.local_dir()`, which `render_instructions`
already appends for every harness, and renames the original. Identical text is adopted once,
by comparing bodies with any existing adopted rule. `cli.py` adds the `init` subparser and the
same unmigrated-home refusal as `status`.

## Files
| File | Change |
|---|---|
| `brainrc/init.py` | new: harness choice, harnesses.local.toml edit, adoption |
| `brainrc/cli.py` | modify: `init` subparser and dispatch |
| `brainrc/__init__.py` | modify: export `init` |
| `docs/install.md`, `README.md` | modify: first-run step |
| `tests/test_init.py` | new |
| `tests/test_cli_args.py` | modify: `init --help` |
| `changelog.d/127-brainrc-init.md` | new |

## Risks
- A user who expected their CLAUDE.md text only in Claude Code gets it in every harness. The output says so; the rule file can be deleted or edited.
- Editing TOML by line could miss an exotic layout (a dotted `claude.enabled` key at the top level). The parse check fails loudly before anything is written.

## Test strategy
Fake HOME with `~/.claude` and `~/.codex`; init, then apply, then check for no CONFLICT and the text in both harnesses' instructions. Unit tests for `set_enabled`. Terminal and non-terminal stdin are faked.

## Tasks
- [x] **T1** [agent: engine] init command, adoption, CLI wiring, tests and docs
  - files: see Files
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7
