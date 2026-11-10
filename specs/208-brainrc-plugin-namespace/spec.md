# Spec: Plugin and marketplace are named brainrc; doctor flags the old plugin

Ticket: gh:208 (epic #199, 5 of 6) · Size: standard · Status: approved

## Problem
Plugin users install `ai-config@ai-config` and get skills as `ai-config:<name>`. After #205 to #207
the tool is `brainrc`, but the manifests, install docs and the role lookup in spec-agent still use the
old plugin name. Renaming changes the install command and every namespaced skill/role name, so
existing users must reinstall, and an old install left beside the new one loads every skill and hook
twice. Text that names the old plugin becomes wrong and must change with the manifests.

## Goals
- Claude Code/Codex, Cursor and Antigravity manifests, and the marketplace, are named `brainrc`.
- Docs and spec-agent tell users and roles the new names, and how to move from `ai-config`.
- `brainrc doctor` warns when the old plugin is still installed (Claude Code, Cursor), alone or next
  to the new one.

## Non-goals
- General wording pass and the `aicfg/` path in docs (#209); only text made wrong by this rename.
- A live `/plugin install brainrc@brainrc`, `codex plugin add` or `agy` run: needs the network and the
  real harnesses, out of scope. Covered offline by AC1 to AC3 (names the harnesses read).
- Doctor changing, uninstalling or cleaning anything; it only reports.
- Doctor detection for Codex and Antigravity (no known on-disk plugin list).
- Hand-editing generated manifests: they come from `python3 scripts/brainrc.py plugin`.

## Acceptance criteria
- **AC1**: Given `python3 scripts/brainrc.py plugin` has run, then `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` (marketplace and its one plugin entry) and `.cursor-plugin/plugin.json`
  have `name` `brainrc`, root `plugin.json` is `{"name": "brainrc"}`, and the author/owner name is
  `brainrc contributors`. No generated manifest contains `ai-config`.
- **AC2**: Given the committed manifests, when `python3 scripts/brainrc.py validate` runs, then it passes
  (no stale or missing manifest), and fails with the `plugin` fix if one still says `ai-config`.
- **AC3**: Given the marketplace and plugin names are both `brainrc`, then the install ids are
  `brainrc@brainrc` (Claude Code, Codex) and skills/roles are `brainrc:<name>`; the test asserts the
  names, since the live install cannot run offline.
- **AC4**: Given the docs, then `docs/install.md`, `README.md` and `docs/troubleshooting.md` give
  `/plugin install brainrc@brainrc`, `codex plugin add brainrc@brainrc`, the Cursor link
  `~/.cursor/plugins/local/brainrc`, `/brainrc:work`, and `brainrc:<name>`; `docs/harness-packages.md`
  and `docs/spec-agent.md` likewise, including the pack `dependencies` example naming core `brainrc`.
  No doc tells a user to install or run `ai-config@ai-config`, `ai-config:<name>` or `/ai-config:work`
  except in the move-from note.
- **AC5**: Given `docs/install.md`, then a short "moving from ai-config" note says to uninstall the old
  plugin (`/plugin uninstall ai-config@ai-config`, then `/plugin marketplace remove ai-config`; for
  Codex, per its docs; remove the old Cursor link) before installing `brainrc@brainrc`, and that skills
  are renamed `brainrc:<name>`.
- **AC6**: Given `skills/spec-agent/SKILL.md`, then it says a Claude Code plugin install names roles
  `brainrc:<role>` and, when `<role>` and `brainrc:<role>` are not found, to try `ai-config:<role>`
  (an old plugin install).
- **AC7**: Given a temp HOME with `~/.cursor/plugins/local/ai-config` (symlink or directory) and no
  `brainrc` entry, when `brainrc doctor` runs, then one WARN names that path, says it is the old
  plugin, and gives the fix (remove it, install `brainrc`). Doctor writes nothing.
- **AC8**: Given AC7 plus `~/.cursor/plugins/local/brainrc`, then the same WARN appears (old next to new).
- **AC9**: Given a temp HOME with only `~/.cursor/plugins/local/brainrc`, or no such directory, then
  doctor emits no Cursor old-plugin finding and does not fail when the directory is absent.
- **AC10**: Given a temp HOME with `~/.claude/plugins/installed_plugins.json` whose `plugins` object has
  the key `ai-config@ai-config`, when `brainrc doctor` runs, then one WARN names the file, says the old
  plugin is installed, and gives the fix `/plugin uninstall ai-config@ai-config`, then
  `/plugin marketplace remove ai-config`. The same WARN appears when `brainrc@brainrc` is also a key
  (old next to new). Doctor does not modify the file or anything else.
- **AC11**: Given a temp HOME where that file is missing, is not valid JSON, is unreadable, has no
  `plugins` object or a non-object one, holds only `brainrc@brainrc` or other keys (including
  `ai-config@other` and `other@ai-config`), then doctor emits no Claude Code old-plugin finding and
  does not error or change its exit code because of the file.
- **AC12**: Given the suite, then AC1 to AC11 run offline on a temp HOME, existing manifest tests are
  updated to the new names, and `python3 -m unittest discover -s tests` and
  `python3 scripts/brainrc.py validate` pass.

## Constraints
- Stdlib-only Python 3.11+, offline; tests use a temp HOME, never the real one.
- Doctor stays read-only; findings keep the (level, what, fix) shape with an actionable fix.
- `installed_plugins.json` is another tool's file: parse tolerantly, match the exact key, never write it.
- Docs only change where the old plugin name is now wrong; the changelog fragment is `bump: minor`-style
  per its README (reinstall needed), chosen by the architect.

## Requirement changes
### Area: plugin-packaging
Purpose: How brainrc is published as a plugin for each harness, and how an old install is flagged.
#### ADDED: Plugin and marketplace are named brainrc
`python3 scripts/brainrc.py plugin` SHALL write the Claude Code/Codex plugin and marketplace, Cursor
plugin and Antigravity `plugin.json` with name `brainrc` and author `brainrc contributors`, so installs
are `brainrc@brainrc` and skills appear as `brainrc:<name>`; `validate` SHALL fail on a stale manifest.
(AC1 to AC3)
#### ADDED: Docs and roles use the new plugin names
Install docs SHALL give the `brainrc` commands and a move-from-`ai-config` note, and spec-agent SHALL
look roles up as `brainrc:<role>`, falling back to `ai-config:<role>`. (AC4 to AC6)
#### ADDED: Doctor warns about the old plugin
`brainrc doctor` SHALL warn, read-only and with the fix, when the old `ai-config` plugin is installed
in Claude Code (key `ai-config@ai-config` in `~/.claude/plugins/installed_plugins.json`) or Cursor
(`~/.cursor/plugins/local/ai-config`), alone or next to `brainrc`, and SHALL stay silent, without
error, when that file is missing, unreadable or of an unexpected shape. (AC7 to AC11)

## Open questions
1. Where does doctor look for an old install? Claude Code: `~/.claude/plugins/installed_plugins.json`
   (key `<plugin>@<marketplace>`, usually under a top-level `plugins` object); Cursor:
   `~/.cursor/plugins/local/<name>`. Codex and Antigravity: no on-disk plugin list is known to the
   repo. *Matters: the ticket says "doctor flags an old install"; guessing a path gives false results.*
   Default taken: detect Claude Code and Cursor only; Codex and Antigravity are NOT detected, and
   install.md's move-from note covers them. The Claude file layout comes from the coordinator, not the
   repo's docs; it is unverified here, hence the tolerant parsing. `known_marketplaces.json` is not read.
2. Old-plugin check by name: any `ai-config` entry in Cursor's local dir is flagged, even a user's own
   plugin of that name. *Matters: false WARN.* Default taken: flag it; the fix says to remove it only if
   it is the old brainrc plugin. For Claude Code the exact key `ai-config@ai-config` narrows this
   (marketplace `ai-config` is the old brainrc one), so it is unlikely to be a user's own plugin.
3. Author/owner string `ai-config contributors` is not named in the ticket. *Matters: manifests and
   tests.* Default taken: rename to `brainrc contributors`.
4. Ticket Files list names `aicfg/`; the package is `brainrc/`. Default taken: `brainrc/plugin.py`,
   `brainrc/doctor.py`.
5. The clone path in docs (`~/ai-config`) and `aicfg/` wording stay for #209; the Cursor link example's
   source dir therefore stays `~/src/ai-config` unless #209 lands first. Default taken: only the
   link name `brainrc` changes here.
6. Ticket text contains no instruction-like content. Nothing quoted.

## Proposed split
Not applicable (standard).
