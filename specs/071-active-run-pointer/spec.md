# Spec: Record the active run's path for external tools

Ticket: gh:71 · Size: standard · Status: draft

## Problem
spec-agent writes a run to `specs/<slug>/` in the repo holding the code. When the session
starts in another directory (a pack repo, a workspace root), tools that look for the current
run in `<cwd>/specs/` find nothing and report no run while one is in progress. Today's
workarounds (move the run and symlink it back, or symlink it in) are manual, per run, and
easy to forget.

## Goals
- spec-agent records where the active run lives, in one well-known place.
- The record is documented as a contract that external tools can rely on.

## Non-goals
- Changing the agent-orchestration mod (not in this repo). Its behavior (item 4 of the ticket)
  is only described by the contract.
- A per-session or multi-run pointer map; concurrent sessions share one pointer, last write wins.
- Clearing or removing the pointer when a run is `done` or abandoned.
- Changing where runs are stored, or moving or symlinking run folders.

## Acceptance criteria
- **AC1**: Given a run in repo A and a session started in another directory B, when the run's
  state is saved, then `$AICFG_HOME/active-run` holds the absolute path of the run directory in A.
- **AC2**: Given `AICFG_HOME` is unset, when the pointer is written, then it is
  `~/.config/ai-config/active-run`.
- **AC3**: Given a pointer is written, then the file is a single line, the path plus a trailing
  newline, and nothing else.
- **AC4**: Given a run at intake, when intake creates the run, then the pointer is written for it.
- **AC5**: Given an existing run, when it resumes (`/work <same ref>` or `/spec-resume`), then
  the pointer is rewritten to that run, replacing any other run's path.
- **AC6**: Given a run reaches `done` or is abandoned, then the pointer still names that run.
- **AC7**: Given the `$AICFG_HOME` directory does not exist yet, when the pointer is written,
  then it is created and the write succeeds.
- **AC8**: Given `references/state.md`, then it documents the file's location, format,
  write moments (intake, resume), persistence after `done`, last-write-wins, and that
  consumers must fall back to `<cwd>/specs/` when the file is absent.

## Constraints
- stdlib-only Python 3.11+ for any code; `$AICFG_HOME` resolves as `aicfg_home()` in
  `aicfg/config.py` does (env var, else `~/.config/ai-config`).
- The pointer is outside the repo, so it is never committed and does not dirty the working tree.
- Absolute path of the run directory only; no secrets or other fields.

## Requirement changes
No `specs/living/` exists, so this creates the area.

### Area: run-pointer
Purpose: Let tools outside a run's repo locate the active spec-agent run.
#### ADDED: Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to
`$AICFG_HOME/active-run` (default `~/.config/ai-config/active-run`) at intake and on every
resume, creating the directory if needed. (AC1, AC2, AC3, AC4, AC5, AC7)
#### ADDED: Pointer persistence
The system SHALL leave the pointer in place when a run reaches `done` or is abandoned. (AC6)
#### ADDED: Pointer contract
The pointer file SHALL be documented in `references/state.md` as the contract for external
tools, including the fallback to `<cwd>/specs/` when it is absent. (AC8)

## Open questions
1. The ticket says "when the run's state is saved" (acceptance criteria) but "at intake, and
   on every resume" (proposal). Is writing at intake and resume enough, or must every
   `state.json` write refresh it? *Matters: with two concurrent sessions, only the per-save
   option keeps the pointer on the session still working.* The spec assumes intake and resume.
2. Who writes the pointer: the engine's instructions only (a documented step the agent
   follows) or a script in spec-agent? *Matters: whether AC1–AC7 are tested by unit test or
   by documented procedure.* Left to the architect.
3. If the pointer cannot be written (read-only home, bad `AICFG_HOME`), should the run
   continue with a warning or stop? *Matters: the pointer is a convenience, so the spec
   assumes warn and continue.*
4. "Abandoned" has no state or stage in `state.md`. Is it just a run that stops without
   `done`? *Matters: AC6 is only testable for `done` otherwise.*
