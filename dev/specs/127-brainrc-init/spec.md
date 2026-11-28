# Spec: brainrc init

Ticket: gh:127 · Size: standard · Status: approved

## Problem
A first `apply` on a machine that already has `~/.claude/CLAUDE.md` or `~/.codex/AGENTS.md`
reports a `CONFLICT` and links nothing there, so the shared rules never load until the user
moves their file by hand, and their own text is then lost from every harness. There is also
no guided way to choose which harnesses brainrc manages: the user edits harnesses.local.toml.

## Goals
- A first-run command that picks the harnesses to manage, interactively or with flags.
- The user's existing instructions keep loading after `init` then `apply`, with no CONFLICT.
- Nothing is deleted: the original file is moved aside, and a link's target is never touched.

## Non-goals
- Content profiles (syncer only, recommended, everything): #173 (E15, "Profiles and excludes")
  owns that mechanism; init will offer them once it exists.
- A managed-block mode that edits the user's file in place: a follow-up.
- Running `apply` from `init`.

## Acceptance criteria
- **AC1**: Given an existing `~/.claude/CLAUDE.md`, when the user runs `init --yes` then `apply`, then apply reports no CONFLICT, `~/.claude/CLAUDE.md` is brainrc's link, and the user's text is in the rendered instructions every harness loads.
- **AC2**: Given installed harnesses, when the user runs `init` in a terminal, then it asks per harness and per instructions file; end of input takes the defaults (manage, adopt). Without a terminal it exits 2 unless `--yes` or `--harness` is given.
- **AC3**: Given `--harness a,b` (or repeated), then harnesses.local.toml gets `enabled = false` for each other managed harness and `enabled = true` for a named one that is disabled or not installed, keeping the rest of the file as it was; an unknown name exits 2 and writes nothing.
- **AC4**: Given an adopted file, then its text goes to `rules/adopted-<harness>.local.md` in the local dir with a comment naming the source, and the original moves to `<file>.bak-brainrc-<UTC time>`. A link the user made is moved as a link; its target is untouched. A link brainrc made is left alone.
- **AC5**: Given the same text in two files, or init run again on a restored file, then the text is adopted once; different text gets `adopted-<harness>-<n>.local.md`. An empty file or dangling link is moved without a rule.
- **AC6**: `--dry-run` writes and moves nothing and prints what it would do; `--no-adopt` leaves instruction files in place and says apply will report each as a CONFLICT.
- **AC7**: `init` is refused, writing nothing, while an old settings home is unmigrated, like `status` and `apply`.

## Requirement changes
### Area: cli-entry-points
#### ADDED: First-run init
`brainrc init` SHALL write the chosen harnesses to harnesses.local.toml (asking in a terminal, or from `--yes` or `--harness`), SHALL adopt each chosen harness's instructions file that apply would report as a CONFLICT by copying its text to `rules/adopted-<harness>.local.md` and moving the original aside, SHALL never delete a file or touch a link's target, and SHALL never run apply. (AC1, AC2, AC3, AC4, AC5, AC6, AC7)

## Open questions
None. Defaults taken under `--oneshot`:
1. Adopted text is a machine-local rule, so it loads in every harness brainrc manages, not only the one it came from. That is how local rules already work, and a user's CLAUDE.md is almost always harness-neutral.
2. Content profiles wait for #173, which owns the profile mechanism; init without them already meets the ticket's done-when.
3. Managed-block mode is a follow-up: adoption already clears the CONFLICT without editing the user's file.
