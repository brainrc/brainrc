Only touch harnesses that are installed, and record them in a manifest

Part of epic #109 (E4), 2 of 6, stacked on #<PR_125>. Retarget to `main` before merging. Closes #126.

## Why
`apply` linked into every enabled harness, so a machine with only Claude Code got `~/.codex`, `~/.cursor`, `~/.config/opencode` and `~/.gemini/config` full of links for tools that aren't there, and `doctor` warned about each one until you disabled it by hand.

## What changed
- `status` and `apply` manage an enabled harness only when its config directory exists: `~/.claude`, `~/.codex`, `~/.config/opencode`, `~/.gemini/config`, `~/.cursor`. That is the rule `doctor` already used. A new optional `home` key in harnesses.toml sets the directory for a harness.
- Skipped harnesses are named in one line, with how to manage one anyway: `enabled = true` in harnesses.local.toml. A harness defined only in that file is managed too.
- `--only` naming a harness that isn't installed exits 2 with the reason.
- `apply` writes `$BRAINRC_HOME/harnesses.json`: each managed harness with its paths, plus the source roots it linked from (old roots kept). Nothing reads it to decide a sync. `uninstall` (#128) and `apply --repair` (#129) build on it.
- `doctor` no longer warns about a harness that isn't installed.
- docs/install.md and the harnesses.toml header explain the rule.

## Acceptance criteria
- [x] AC1: a claude-only HOME gets only `~/.claude` changes. Verified by `InstalledHarnessTest`.
- [x] AC2: skipped harnesses are named; `status` writes nothing. Verified by `InstalledHarnessTest`.
- [x] AC3: `enabled = true`, a local-only harness and `home` work. Verified by `InstalledHarnessTest` and `ConfigErrorTest`.
- [x] AC4: a later install is picked up; a removed harness is never recreated. Verified by `InstalledHarnessTest`.
- [x] AC5: `--only` a missing harness exits 2. Verified by `InstalledHarnessTest`.
- [x] AC6: the manifest lists managed harnesses and roots. Verified by `InstalledHarnessTest`.
- [x] AC7: `doctor` is clean on a claude-only HOME. Verified by `InstalledHarnessTest` and `DoctorTest`.

## How to verify
```
python3 -m unittest tests.test_installed_harnesses
python3 -m unittest discover -s tests
HOME=$(mktemp -d) sh -c 'mkdir "$HOME/.claude" && python3 scripts/brainrc.py apply && ls -A "$HOME"'
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Spec, Plan, Deliver. See `specs/126-installed-harnesses/log.md`.
- "Installed" means the config directory exists, not that a binary is on PATH: the directory is what brainrc writes into, and it's what `doctor` already checked.
- Links an older apply already made for a harness that isn't installed are left alone: they can only exist if that directory exists, which makes the harness count as installed.
- The manifest is a record, never an input, so a broken or stale one can't change what gets synced.
- Test fixtures that apply into a fake HOME now create every harness directory first.

## Follow-ups
- None.

Spec: `specs/126-installed-harnesses/spec.md` · Plan: `specs/126-installed-harnesses/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
