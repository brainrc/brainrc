# Campaign gh:120 · native Windows (E16)

## 2026-11-26T22:50:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:120 --shape ordered --dry-run`, worked by hand: the skill ships in
brainrc/gatework, which isn't installed in the build environment.

- Members, all open on GitHub at the start: #177 (copy mode instead of symlinks), #178 (native
  hook commands), #179 (a Windows CI cell). #342 (tests that run on Windows) is also open under
  the epic; the suite already passes on the Windows runner, and what it has left (dropping
  `continue-on-error` from the Windows cells) is #179's job, so it is folded into #179.
- Shape: `ordered`, as the brief asks. Order: #177, #178, #179, from the epic body (`body`):
  hooks are written into the files copy mode installs, and the CI cell runs both.
- Delivery: `sequential`. One branch is pushable here, so each child's PR opens from it once the
  one before has merged, with `main` merged in first.
- Starts from `main` at dc5e22b (v0.8.35).

## engine · Campaign gate · approved
The coordinator's brief passes on the maintainer's "Start E16", with the decision of Nov 26 that
everything stays Python 3.11+, stdlib only, with no compiled code. Recorded as approved on that
basis. Merging, tagging, releasing and closing #120 stay with the maintainer.

## engine · gh:177 · Spec and Plan
- `link_mode` in `brainrc.local.toml` (`auto`, the default; `symlink`; `copy`), and
  `BRAINRC_LINK_MODE` over it for one run. `auto` links on POSIX, and on Windows tries one
  symlink in a temporary directory and copies when that fails.
- `brainrc/copies.py` places each item (a link, or a copy written beside it and renamed into
  place) and records every copy in the settings home's `copies.json`: harness, source, a digest
  of the source when copied, and a digest of what was written.
- `Link.state` reads the record: `update` when the source changed or the mode did, and a new
  `edited` state when the copy no longer matches what apply wrote. Apply never overwrites an
  edited copy and counts it as a conflict; uninstall renames it to a `*.bak-brainrc-*` backup
  (`SETASIDE`) and removes the rest. Prune, doctor and init read the record too.
- OpenCode's plugin finds the guard hooks from its own real path; its copy has that expression
  replaced with the source's path (`Adapter.copied_file`).
- POSIX output is unchanged: the goldens in `tests/test_adapter_goldens.py` still pass as they
  were. Project scope already writes files, and the lock and frozen installs are untouched.
- Plan: `brainrc/copies.py` (new), `plan.py`, `cli.py`, `doctor.py`, `uninstall.py`, `init.py`,
  `config.py`, `adapters/base.py`, `adapters/opencode.py`; docs in `configuration.md`,
  `install.md`, `troubleshooting.md`; tests in `tests/test_copy_mode.py`.

## engine · gh:177 · Built
Verified with the goldens unchanged, `validate` passing and the full suite passing.

## engine · gh:177 · Review
A high-effort code review of the diff found six bugs and three nits, all fixed before the push:
- A copied hooks dir couldn't find Claude Code's guards (each tool's `guard.py` looks beside its
  own real path). Every copied Python file that does that is now told its source's real path, so
  a copy behaves as the link did; a test runs the copied Codex guard and gets its deny.
- uninstall didn't put back the instructions file init moved aside, when a copy sat there.
- Prune compared unnormalized paths with the record's keys.
- `place` deleted the old item before the copy was made, so a failure lost it; it now builds the
  copy beside it first. Python's `ignore_dangling_symlinks` reads a relative link's target from
  the working directory and drops good links (Gatework's `roles`), so dangling links are skipped
  by hand instead.
- uninstall deleted `copies.json` even when a copy's removal failed; it now drops only the records
  of copies that are gone (`FORGET`).
- init's project import didn't skip apply's copies.
- Nits: doctor's reason after a switch back to links, the record's temporary file name in
  `--purge`'s list, and reading the mode and record once per run.

## engine · gh:178 · Spec and Plan
On Windows, apply writes each core hook command as one Python call that does what the POSIX line
did (pass, or print the tool's allow JSON, when the guard is gone), with no shell syntax in it:
`py -3 -I -c "import os,runpy,sys;f='C:/.../guard.py';..."`. `-I` keeps a module in the project
folder from being imported. Where the line goes comes from each tool's docs (`windows_hook` in
`brainrc/adapters/`): Claude Code's exec form (no shell), Codex's `commandWindows`, Copilot's
`powershell`, `command` for Cursor (PowerShell), Junie (cmd), Gemini, Devin, Kiro and
Antigravity. Python is `py -3`, then `python`, then the interpreter brainrc runs under. A hooks
path a shell would read is a config error naming `hooks_dir`. POSIX output is unchanged (goldens).
- Plan: `brainrc/hookcmd.py` (new), `plan.py`, `settings.py`, `doctor.py`, the adapters,
  `overrides/opencode/plugin.js` (`py -3`/`python` on win32); docs in `install.md`; tests in
  `tests/test_windows_hooks.py`.
- Unverified: Codex's `commandWindows` and Copilot's `powershell` come from parts of their
  reference pages; Gemini, Devin, Kiro and Antigravity don't say which shell runs a hook on
  Windows, so their line is built to mean the same in cmd, PowerShell and Git Bash.

## engine · gh:178 · Built
Verified with the goldens unchanged, `validate` passing and the full suite passing.

## engine · gh:178 · Review
A high-effort code review found four Windows bugs and two nits, all fixed:
- doctor read Codex's and Copilot's POSIX `command` first, with a `$HOME` that cmd and PowerShell
  don't set, and reported their guards missing. It now reads the Windows field first and expands
  `$HOME` itself.
- With no `py` or `python` on PATH, a Python path with a space was quoted in a way PowerShell and
  cmd read differently, for tools whose shell is unknown. That is now a config error that says to
  install the py launcher, and a Python path a shell would read is refused too.
- The Python chosen could be the Microsoft Store stub or older than 3.11. Each one found is now run
  once to check it, and `python` is written as a full path (only the launcher by name).
- `-I` ignores `PYTHONUTF8`, so a guard read a non-ASCII payload in the ANSI code page and could
  fail open. Hooks and doctor now pass `-X utf8`.
- Nits: doctor spread a string `args` into letters; the changelog fragment for this PR is written
  when the branch restarts after #392.
