# run-pointer

Let tools outside a run's repo locate the active spec-agent run.

### Active run pointer
The system SHALL write the absolute path of the active run directory as a single line to
`active-run` in the settings home (default `~/.config/brainrc/active-run`) at intake, on every
resume, and on every checkpoint commit (each gate, block, and done), creating the directory if
needed, via `skills/spec-agent/scripts/active_run.py write`. The run directory SHALL be the
`specs/<slug>` inside the run's worktree. A write failure SHALL warn on stderr and exit 0. In an
ordered campaign the pointer SHALL name the child currently in progress. (AC5)
_Last changed by 255-run-worktrees._

### Pointer read
`active_run.py read` SHALL return the pointer's run if the file exists and names an existing
directory, else the newest run by `state.json` mtime among `<cwd>/specs/` and the `specs/` of every
branch worktree listed by `git worktree list`, skipping detached worktrees. (AC6)
_Last changed by 255-run-worktrees._

### Pointer persistence
The system SHALL leave the pointer in place when a run reaches `done` or is abandoned (stops
without reaching `done`). (AC7)
_Last changed by 071-active-run-pointer._

### Pointer contract
The pointer file SHALL be documented in `references/state.md` as the contract for external
tools, including the fallback to `<cwd>/specs/` when it is absent. (AC12)
_Last changed by 071-active-run-pointer._
