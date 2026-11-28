# Spec: Record the active run's path for external tools

Ticket: gh:71 · Size: standard · Status: approved

## Problem
spec-agent writes a run to `specs/<slug>/` in the repo holding the code. When the session
starts in another directory (a pack repo, a workspace root), tools that look for the current
run in `<cwd>/specs/` find nothing and report no run while one is in progress. Today's
workarounds (move the run and symlink it back, or symlink it in) are manual, per run, and
easy to forget.

## Goals
- spec-agent records where the active run lives, in one well-known place.
- The record is documented as a contract that external tools can rely on.
- A small script writes and reads the pointer, so behavior is unit-testable.

## Non-goals
- Changing the agent-orchestration mod (not in this repo). Its behavior (item 4 of the ticket)
  is only described by the contract.
- A per-session or multi-run pointer map; concurrent sessions share one pointer, last write wins.
- Clearing or removing the pointer when a run is `done` or abandoned.
- Changing where runs are stored, or moving or symlinking run folders.

## Acceptance criteria
- **AC1**: Given a run in repo A and a session started in another directory B, when a write
  moment occurs, then `$AICFG_HOME/active-run` holds the absolute path of the run directory in A.
- **AC2**: Given `AICFG_HOME` is unset, when the pointer is written, then it is
  `~/.config/ai-config/active-run`.
- **AC3**: Given a pointer is written, then the file is a single line, the path plus a trailing
  newline, and nothing else.
- **AC4**: Given a new run, when intake creates it, then the pointer is written for it.
- **AC5**: Given an existing run, when it resumes (`/work <same ref>` or `/spec-resume`), then
  the pointer is rewritten to that run, replacing any other run's path.
- **AC6**: Given a run, when a checkpoint commit is made (each gate, block, and `done`), then
  the pointer is rewritten to that run.
- **AC7**: Given a run reaches `done` or is abandoned (stops without reaching `done`), then the
  pointer still names that run and no cleanup occurs.
- **AC8**: Given the `$AICFG_HOME` directory does not exist yet, when the pointer is written,
  then it is created and the write succeeds.
- **AC9**: Given `skills/spec-agent/scripts/active_run.py`, then it offers `write` and `read`;
  `read` prints the pointer's run when the file exists and names an existing directory.
- **AC10**: Given the pointer file is absent or names a directory that does not exist, when
  `read` runs, then it returns the newest run in `<cwd>/specs/` by `state.json` mtime.
- **AC11**: Given the pointer cannot be written (read-only home, bad `AICFG_HOME`), when `write`
  runs, then it warns on stderr and exits 0, and the run continues.
- **AC12**: Given `references/state.md`, then it documents the file's location, format, write
  moments (intake, resume, every checkpoint commit), persistence after `done`, last-write-wins,
  and that consumers must fall back to `<cwd>/specs/` when the file is absent.

## Constraints
- stdlib-only Python 3.11+; `$AICFG_HOME` resolves as `aicfg_home()` in `aicfg/config.py`
  does (env var, else `~/.config/ai-config`).
- The pointer is outside the repo, so it is never committed and does not dirty the working tree.
- Absolute path of the run directory only; no secrets or other fields.

## Requirement changes
No `specs/living/` exists, so this creates the area.

### Area: run-pointer
Purpose: Let tools outside a run's repo locate the active spec-agent run.
#### ADDED: Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to
`$AICFG_HOME/active-run` (default `~/.config/ai-config/active-run`) at intake, on every
resume, and on every checkpoint commit (each gate, block, and done), creating the directory if
needed, via `skills/spec-agent/scripts/active_run.py write`. A write failure SHALL warn on
stderr and exit 0. (AC1-AC6, AC8, AC9, AC11)
#### ADDED: Pointer read
`active_run.py read` SHALL return the pointer's run if the file exists and names an existing
directory, else the newest run in `<cwd>/specs/` by `state.json` mtime. (AC9, AC10)
#### ADDED: Pointer persistence
The system SHALL leave the pointer in place when a run reaches `done` or is abandoned (stops
without reaching `done`). (AC7)
#### ADDED: Pointer contract
The pointer file SHALL be documented in `references/state.md` as the contract for external
tools, including the fallback to `<cwd>/specs/` when it is absent. (AC12)

## Open questions
None.
