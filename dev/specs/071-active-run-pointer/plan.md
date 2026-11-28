# Plan: Record the active run's path for external tools

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none (stdlib only)
- **Public API / contract changes:** new file contract `$AICFG_HOME/active-run` (one absolute path + `\n`) and new CLI `skills/spec-agent/scripts/active_run.py write|read`; external tools (the orchestration mod) may rely on both
- **Migrations / data changes:** none; the pointer lives outside the repo, nothing to roll back
- **Security triggers touched:** none (writes one file under the user's config dir; no secrets)
- **Domains:** scripting
- **Environments affected on deploy:** none; takes effect on the next `aicfg apply` / plugin install
- **Destructive or replacing changes:** none

## Approach
New script `skills/spec-agent/scripts/active_run.py`, modeled on `living_specs.py`: module
docstring as usage, `argparse` subcommands, `main(argv) -> int`, stdlib only. It cannot import
`aicfg` (skills are installed without the package), so it copies `aicfg_home()` from
`aicfg/config.py` in three lines: `$AICFG_HOME` expanded with `expanduser`/`expandvars` (as
`config.expand`), else `Path.home() / ".config/ai-config"`.

`write <run-dir>`: resolve to an absolute path, `mkdir(parents=True, exist_ok=True)` the home,
write `<path>\n` to a temp file in the same directory and `os.replace` it, so a concurrent
reader never sees a partial line (last write wins). Any `OSError` prints `WARN ...` to stderr
and returns 0 (AC11). `read`: if the pointer exists and its stripped line is an existing
directory, print it; else print the parent of the newest `<cwd>/specs/*/state.json` by mtime;
if neither, print nothing to stdout, a note to stderr, and return 1 (unspecified by the spec;
lets callers distinguish "no run").

The engine calls `write` at the moments the docs name. Rather than repeating it everywhere, the
call is attached to the two places that already define those moments: the checkpoint-commit
rule in `references/state.md` (covers every gate, block, and done: AC6, AC7) and intake/resume
(`lifecycle.md` § 0 step 4, `state.md` § Resume). Nothing clears the pointer (AC7).

## Files
| File | Change |
|---|---|
| `tests/test_active_run.py` | new: subprocess tests against the CLI, temp `AICFG_HOME`/`HOME`/cwd |
| `skills/spec-agent/scripts/active_run.py` | new: `write` / `read` |
| `skills/spec-agent/references/state.md` | modify: `## Active run pointer` contract section; checkpoint rule and Resume call `write` |
| `skills/spec-agent/references/lifecycle.md` | modify: intake step writes the pointer |
| `skills/spec-agent/SKILL.md` | modify: call `active_run.py write` in Run step 1 (intake, resume) and step 3 (every checkpoint commit); contract stays in `state.md` |
| `changelog.d/071-active-run-pointer.md` | new: `bump: patch` fragment |

## Risks
- The engine (a model) forgets a write moment, mitigated by tying `write` to the existing checkpoint rule instead of a separate step.
- Tests touch the real `~/.config`, mitigated by always setting `AICFG_HOME` or `HOME` to a temp dir in the subprocess env.
- Docs grow context load, mitigated by keeping the contract section under ~15 lines.

## Test strategy
Unit tests in `tests/test_active_run.py` (style of `tests/test_living_specs.py`: run the script
via `subprocess` with `sys.executable`, temp dirs). AC1-3, 8-11 automated. AC4-7 and AC12 are
doc behavior: verified by reading `state.md`/`lifecycle.md` diffs, plus a test that `write`
replaces an earlier pointer (AC5) and that nothing removes it. Full suite + `aicfg.py validate`.

## Tasks
- [ ] **T1** [agent: test-writer] Contract tests for `active_run.py`
  - files: `tests/test_active_run.py`
  - criteria: AC1, AC2, AC3, AC5, AC8, AC9, AC10, AC11
  - review: each
- [ ] **T2** [agent: implementer] Implement `active_run.py write|read` to pass T1
  - files: `skills/spec-agent/scripts/active_run.py`
  - criteria: AC1, AC2, AC3, AC5, AC8, AC9, AC10, AC11
  - review: each
  - after: T1
- [ ] **T3** [agent: implementer] Document the pointer contract and write moments; changelog fragment
  - files: `skills/spec-agent/references/state.md`, `skills/spec-agent/references/lifecycle.md`, `skills/spec-agent/SKILL.md`, `changelog.d/071-active-run-pointer.md`
  - criteria: AC4, AC5, AC6, AC7, AC12
  - review: each
