# Plan: Doctor detects double installs

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** none (a new WARN)
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
`doctor_findings` already computes every planned link's state; it now records which harnesses
have a link in place. A new `_double_install_findings(linked)` reads Claude Code's plugin list
through the guarded reader the old-plugin check used (factored out as `_read_json` and
`_claude_plugins`), skips a plugin disabled in `enabledPlugins`, and checks Cursor's local
plugin path.

## Files
| File | Change |
|---|---|
| `brainrc/doctor.py` | modify |
| `tests/test_doctor_plugin.py` | modify: `DoubleInstallTest`, `DoubleInstallDoctorTest` |
| `docs/troubleshooting.md` | modify |
| `changelog.d/130-doctor-plugin-overlap.md` | new |

## Risks
- A plugin installed under another name isn't recognised; the plugin's own name is `brainrc`.

## Test strategy
Unit tests on a temp HOME for each case, and one through a real apply and `doctor_findings`.

## Tasks
- [x] **T1** [agent: engine] double-install warning, tests and docs
  - files: see Files
  - criteria: AC1, AC2, AC3
