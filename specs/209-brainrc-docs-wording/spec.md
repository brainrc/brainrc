# Spec: Rename docs and wording pass

Ticket: gh:209 (epic #199, 6 of 6) · Size: standard · Status: draft

## Problem
After #205-#208 the code, settings home, hooks, backups and plugin are `brainrc`, but users still meet
`aicfg` and `ai-config` first: in the README, install and tutorial docs, usage and error text,
comments, skills and the example pack. About 800 lines still name the old tool. Some must stay
(shims, detection of old installs); nothing today separates those from leftovers.

## Goals
- Every place that names the tool says `brainrc`, except a closed, checkable allowlist of deliberate compatibility.
- The old-name support window is stated for users: old names work until 0.5.0 (`SHIM_REMOVED_IN`).

## Non-goals
- Editing `CHANGELOG.md` history or anything under `specs/` except `spec.md`, living specs aside (below).
- Removing or changing old-name behavior (shims, `AICFG_HOME`, legacy home, `migrate`, old-plugin doctor warning).
- Renaming on-disk names written into users' files (see the allowlist and open question 3).

## Acceptance criteria
- **AC1**: Given a case-insensitive search for `aicfg|ai-config` over the whole repo except `CHANGELOG.md`, `changelog.d/`, `specs/` and `.git/`, when it runs, then every hit matches an allowlist entry (AC2), and a test fails otherwise.
- **AC2**: Given the allowlist (one data table in a test, each entry = path glob + regex + reason), when the test runs, then an entry that matches no line fails the test (no stale entries), and entries cover only categories A-F:
  - A. Shim files, whole file: `aicfg/**`, `scripts/aicfg.py`, `scripts/check_install.py`, `tests/` files that exercise old names.
  - B. Packaging: the `aicfg` console script line and the `"aicfg"` package entry in `pyproject.toml`; the CI step that runs the deprecated script.
  - C. Old-install detection or migration in code: `AICFG_HOME`, legacy `~/.config/ai-config`, `OWNED_HOOK`'s `ai-config` dirs, `.bak-aicfg-*`, `ai-config@ai-config`, `~/.cursor/plugins/local/ai-config`, `aicfg_env`, in `brainrc/`, `skills/spec-agent/scripts/active_run.py`.
  - D. On-disk names kept for compatibility: Codex MCP block markers, OpenCode `ai-config-guard.js` link, `.git/aicfg-fetched.json`.
  - E. Docs sentences about old names: `docs/install.md` "Moving from ai-config" and upgrade notes, `docs/troubleshooting.md` old-plugin and `AICFG_HOME` entries, the old-name fallbacks in `skills/spec-agent/SKILL.md` and `references/state.md`; each such sentence says old, former, deprecated or legacy.
  - F. The allowlist test itself.
- **AC3**: Given `brainrc` usage, `--help`, doctor, status, apply, validate and error text, when printed, then they name `brainrc` (and `scripts/brainrc.py`), never `aicfg`/`ai-config`, except the deprecation lines of C.
- **AC4**: Given README, AGENTS.md, CONTRIBUTING.md, `docs/`, `examples/pack-acme`, skills, agents, rule files, `mcp/servers.toml`, `harnesses.toml`, `packs.toml`, `.pre-commit-config.yaml`, generated-file banners, guard messages and code comments/docstrings, when read, then commands and the checkout dir are `brainrc` and `scripts/brainrc.py`.
- **AC5**: Given `docs/tutorial.md`, when `specs/013-tutorial/run-tutorial.sh` runs (it extracts every bash block, uses a fresh local clone and temp HOME, needs no network), then it exits 0 and the tutorial commands use `scripts/brainrc.py` and `~/.config/brainrc/`. CI or the test suite runs it, or the spec's verify step records its result.
- **AC6**: Given the changelog fragment `changelog.d/<branch>.md`, when read, then it is marked **[pack contract]**, lists the renamed docs and wording, and says `aicfg`/`ai-config` names keep working with warnings until 0.5.0 and are removed then.
- **AC7**: Given `python3 scripts/brainrc.py validate` and the full unit tests, when run, then both pass, and behavior of the old-name paths in C is unchanged.
- **AC8**: Given the living specs, when read, then they say `brainrc` where they said `aicfg` (wording only).

## Constraints
- Offline only. No new dependencies. Files stay short.
- Generated files (`dist/`, `.claude-plugin/`, `.cursor-plugin/`, root `plugin.json`) are regenerated, not edited.
- Old-name behavior must not change; only the allowlisted spots keep the words.

## Requirement changes
### Area: cli-entry-points
#### ADDED: Old names live only in an allowlist
The system SHALL name itself `brainrc` in all user-facing text, and SHALL keep `aicfg`/`ai-config` only in a test-enforced allowlist of compatibility spots. (AC1, AC2, AC3, AC4)
#### ADDED: Old-name support window is published
The changelog SHALL state, as a **[pack contract]** note, that old names work until 0.5.0. (AC6)
#### MODIFIED: Deprecated aicfg names
Unchanged behavior; the line "Existing living requirements mention `aicfg` commands by name; their wording is left to #209" is dropped. (AC8)
### Area: aicfg-apply
Wording only (`aicfg` to `brainrc`; behavior unchanged; file name kept, open question 2):
#### MODIFIED: Symlinked config files
`brainrc apply` replaces `aicfg apply`. (AC8)
#### MODIFIED: One apply at a time
`brainrc apply` replaces `aicfg apply`. (AC8)
#### MODIFIED: No lost concurrent writes
`brainrc apply` replaces `aicfg apply`. (AC8)
### Area: aicfg-config
Wording only (name `brainrc`, behavior unchanged):
#### MODIFIED: Readable config errors
`brainrc` replaces `aicfg`. (AC8)
#### MODIFIED: Unknown config names warn
`brainrc` replaces `aicfg`. (AC8)
#### MODIFIED: Closed output
`brainrc` replaces `aicfg`. (AC8)
#### MODIFIED: Unique pack names
`brainrc` replaces `aicfg`. (AC8)
#### MODIFIED: Apply checks packs first
`brainrc status` and `brainrc apply` replace the `aicfg` commands. (AC8)
#### MODIFIED: Git packs follow their config
`brainrc apply`, `status` and `doctor` replace the `aicfg` commands. (AC8)
#### MODIFIED: Git calls time out
`brainrc` replaces `aicfg`. (AC8)
#### MODIFIED: Agent model and tool names
`brainrc validate` replaces `aicfg validate`. (AC8)

## Open questions
No decisions are taken before Deliver; each default below is what the run does and lists at Deliver.
1. Tests: keep old-name tests and allow `tests/` wholesale? *Why: the grep must stay a real test.* Default: rename `tests/test_aicfg.py` to `tests/test_brainrc.py`, rename internal identifiers (`aicfg_home` to `settings_home`, `aicfg_env` to `legacy_env`, `*.aicfg-tmp-*` temp names), and allowlist only tests that exercise old names, by file.
2. Rename living files `aicfg-apply.md`/`aicfg-config.md`? *Why: they are under specs/, outside the grep; renaming loses `Last changed by` history links.* Default: keep the names, fix the body wording (AC8).
3. Rename the three on-disk names of D (Codex markers, OpenCode link, fetch record)? *Why: users' files hold them; renaming needs old-marker recognition, pruning and tests, which is behavior change beyond a wording ticket.* Default: keep, allowlist by exact pattern, note a follow-up in the changelog fragment.
4. Verify the tutorial in CI? *Why: AC5 must be re-checkable.* Default: run `specs/013-tutorial/run-tutorial.sh` at verify and record the output; no new CI job.
5. Size: standard, no split (~50 files, mostly mechanical). *Why: a bigger size adds ceremony.* Default: standard.
