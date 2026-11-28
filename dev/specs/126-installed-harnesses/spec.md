# Spec: Only touch harnesses that are installed

Ticket: gh:126 · Size: standard · Status: approved

## Problem
`brainrc apply` links into every enabled harness, so a machine with only Claude Code ends up with
`~/.codex`, `~/.cursor`, `~/.config/opencode` and `~/.gemini/config` full of links for tools that
aren't there. Users have to disable each one by hand, and `doctor` warns about each until they do.
Nothing records which harnesses brainrc manages, which `uninstall` and `--repair` will need.

## Goals
- `apply` creates nothing for a harness that isn't installed.
- The user can see what was skipped and can force a harness anyway.
- apply keeps a manifest of the harnesses it manages.

## Non-goals
- Detecting a harness from its binary on PATH (a config dir is what brainrc writes into).
- Removing what an older apply already created for a harness that isn't installed.
- `init` (#127) and `uninstall` (#128), which build on the manifest.

## Acceptance criteria
- **AC1**: Given a fresh HOME with only `~/.claude`, when the user runs `apply`, then only `~/.claude` and `~/.claude.json` change, and a second `status` is in sync.
- **AC2**: Given enabled harnesses that aren't installed, when `status` or `apply` runs, then the output names each one with the directory it looked for and how to manage it anyway; `status` still writes nothing.
- **AC3**: Given `enabled = true` for a harness in harnesses.local.toml, or a harness defined only there, then it is managed even when not detected; a `home` key sets the directory that counts as installed.
- **AC4**: Given a harness installed after the first apply, then the next apply manages it; given its directory removed, then apply never recreates it.
- **AC5**: Given `--only` naming a harness that isn't installed, then it exits 2 with the reason and writes nothing.
- **AC6**: Given apply, then `$BRAINRC_HOME/harnesses.json` lists the managed harnesses with their paths and the source roots; `--only` keeps entries outside its scope, a full apply drops harnesses no longer managed, and old roots are kept after the checkout moves.
- **AC7**: Given a harness that isn't installed, then `doctor` reports nothing about it, and a fresh claude-only HOME is clean after apply.

## Constraints
Stdlib only. No change for machines where every enabled harness is installed.

## Requirement changes
### Area: aicfg-apply
#### ADDED: Only installed harnesses
`brainrc apply` and `status` SHALL manage an enabled harness only when its home directory exists (the `home` key, else the parent of its `instructions` or `skills` path) or harnesses.local.toml enables it explicitly or defines it; they SHALL name each skipped harness, and SHALL never create a skipped harness's files. (AC1, AC2, AC3, AC4, AC5)
#### ADDED: Harness manifest
`brainrc apply` SHALL write `<settings home>/harnesses.json` listing each managed harness's paths and the source roots it linked from, keeping entries outside `--only` and earlier roots. (AC6)
### Area: doctor
#### ADDED: Skipped harnesses are not findings
`brainrc doctor` SHALL check only the harnesses apply manages, and SHALL report nothing for an enabled harness that isn't installed. (AC7)

## Open questions
None. Defaults taken under `--oneshot`:
1. Installed means the harness's config directory exists, the same rule `doctor` already used; no PATH lookup.
2. A harness defined only in harnesses.local.toml is the user's own and is managed without detection.
3. The manifest is a record, not an input: what apply syncs still comes from harnesses.toml and detection, so a stale or broken manifest can't change a sync.

## Proposed split
