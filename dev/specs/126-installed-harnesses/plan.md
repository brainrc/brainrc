# Plan: Only touch harnesses that are installed

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** additive: optional `home` key in harnesses.toml; new file `$BRAINRC_HOME/harnesses.json`. Behavior change: harnesses that aren't installed are skipped instead of created.
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
`config.load_harnesses()` (the enabled view every planner reads) drops enabled harnesses that
aren't installed, unless harnesses.local.toml forces them; `include_missing=True` keeps them.
`harness_home()` gives the directory to test (`home`, else the parent of `instructions` or
`skills`, as doctor did). So `plan()`, `mcp_plan()`, `doctor` and `--only` all follow one rule.
A skipped harness falls on the disabled side of `plan()`; with no directory it has nothing to
prune or merge. `_sync` prints one "Skipped, not installed" line and, on apply, writes the
manifest through a new `brainrc/manifest.py`. `doctor` loses its own not-installed check.
Test fixtures that apply into a fake HOME now create every harness's directory first.

## Files
| File | Change |
|---|---|
| `brainrc/config.py` | modify: installed detection, `home` key, forced harnesses, `missing_harnesses()` |
| `brainrc/manifest.py` | new: read and update `harnesses.json` |
| `brainrc/cli.py` | modify: skipped line, write the manifest |
| `brainrc/doctor.py` | modify: drop the not-installed warning |
| `harnesses.toml`, `docs/install.md` | modify: document detection and the manifest |
| `tests/test_installed_harnesses.py` | new |
| `tests/test_brainrc.py`, `tests/test_cli_args.py`, `tests/test_migrate.py`, `tests/test_doctor_paths.py` | modify: fixtures install the harnesses |
| `changelog.d/126-installed-harnesses.md` | new |

## Risks
- An install whose harness dir doesn't exist yet but is wanted (a brand-new Cursor) is skipped until the dir exists; the output says so and how to force it.
- Antigravity counts as installed by `~/.gemini/config`, the path doctor already used; a `home` override covers a different layout.

## Test strategy
Fake-HOME unit tests with only `~/.claude`; the existing suites run with every harness directory present.

## Tasks
- [x] **T1** [agent: engine] Installed detection, skipped line, manifest, doctor, tests and docs
  - files: see Files
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7
