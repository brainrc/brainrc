# Verify: Render rules and extensions to $AICFG_HOME

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_defaults_to_config_dir_under_home`, `test_apply_renders_into_aicfg_home`; real `apply` in a fake HOME: `~/.config/ai-config/{instructions,extensions}.md` written | pass |
| AC2 | `test_old_dist_link_is_updated_and_old_file_removed` (status `UPDATE`, link re-pointed), `test_disabled_harness_link_to_aicfg_home_is_pruned`; real upgrade run: `UPDATE claude ~/.claude/CLAUDE.md`, then the link points to `$AICFG_HOME/instructions.md` | pass |
| AC3 | same test: `dist/instructions.md` and the emptied `dist/` removed (red first); real upgrade run removed the file | pass |
| AC4 | `SKILL.md` § Packs, `lifecycle.md`, `ticket-jira`: `$AICFG_HOME/extensions.md`, falling back to `references/extensions.md`; `campaign.md` names `extensions.md` without a path, no change needed | pass |
| AC5 | `test_doctor_names_the_home_render` (stale render reported with the `~` path); DoctorTest render tests updated; real `doctor` after apply: `No problems found.` | pass |
| AC6 | README, `harnesses.toml`, `docs/architecture.md`, `docs/packs.md`, `docs/troubleshooting.md`, `docs/tutorial.md`; no old paths left outside specs/CHANGELOG (grep) | pass |
| AC7 | 6 new tests (red first on a stub returning the old path), existing tests moved off `dist/` with an isolated `AICFG_HOME`; `specs/013-tutorial/run-tutorial.sh` → `tutorial ran clean`; VERSION 0.3.16; CHANGELOG **[pack contract]**, non-breaking; `aicfg plugin` run | pass |

## Commands
- `python3 -m unittest discover -s tests -q` → OK
- `python3 scripts/aicfg.py validate` → OK; `validate --pack examples/pack-acme` → OK
- `bash specs/013-tutorial/run-tutorial.sh` → tutorial ran clean
