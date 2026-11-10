# Plan: Fix doc drift

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** none (doctor prints text; it runs no command)
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Add `shell_path(path)` to `brainrc/doctor.py`: `tilde(path)`, then `shlex.quote` the part after
`~/` (or the whole path when it isn't under home). Use it in the three `rm` fixes. Replace the
install guide's pin with a placeholder. A new test module scans the install docs for release pins
against `VERSION`. Reword `overrides/README.md` from `harnesses.toml`, and the "public" lines.

## Files
| File | Change |
|---|---|
| `brainrc/doctor.py` | modify: `shell_path`, used by the three `rm` fixes |
| `tests/test_doctor_paths.py` | new |
| `tests/test_doc_versions.py` | new |
| `docs/install.md`, `overrides/README.md`, `AGENTS.md`, `README.md` | modify |
| `changelog.d/105-fix-doc-drift.md` | new |

## Risks
- README and AGENTS.md lines also change in the open E6 PRs (#257–#262): a one-line conflict at most.

## Test strategy
Unit tests: `shell_path` round-trips through `sh`; doctor findings with spaced paths; the doc
scanner on the real docs and on a stale sample.

## Tasks
- [ ] **T1** [agent: implementer] Quote doctor's rm paths, drop the stale pin, fix the docs, add the doc test
  - files: `brainrc/doctor.py`, `tests/test_doctor_paths.py`, `tests/test_doc_versions.py`, `docs/install.md`, `overrides/README.md`, `AGENTS.md`, `README.md`, `changelog.d/105-fix-doc-drift.md`
  - criteria: AC1, AC2, AC3, AC4, AC5
