# run-pointer

Let tools outside a run's repo locate the active spec-agent run.

### Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to
`$AICFG_HOME/active-run` (default `~/.config/ai-config/active-run`) at intake, on every
resume, and on every checkpoint commit (each gate, block, and done), creating the directory if
needed, via `skills/spec-agent/scripts/active_run.py write`. A write failure SHALL warn on
stderr and exit 0. (AC1-AC6, AC8, AC9, AC11)
_Last changed by 071-active-run-pointer._

### Pointer read
`active_run.py read` SHALL return the pointer's run if the file exists and names an existing
directory, else the newest run in `<cwd>/specs/` by `state.json` mtime. (AC9, AC10)
_Last changed by 071-active-run-pointer._

### Pointer persistence
The system SHALL leave the pointer in place when a run reaches `done` or is abandoned (stops
without reaching `done`). (AC7)
_Last changed by 071-active-run-pointer._

### Pointer contract
The pointer file SHALL be documented in `references/state.md` as the contract for external
tools, including the fallback to `<cwd>/specs/` when it is absent. (AC12)
_Last changed by 071-active-run-pointer._
