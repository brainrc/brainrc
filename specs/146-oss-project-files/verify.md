# Verify: Open-source project files

Run at 2026-11-03T05:55:04Z on commit `c41a116`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 725 ran, 0 failed, 1 skipped (`OK (skipped=1)`, exit 0). Log: `/tmp/claude-0/-home-user/0dcec93d-71ed-51cf-87d5-99510717abc8/scratchpad/verify146/test.log` |
| Targeted tests (verbose) | `python3 -m unittest -v tests.test_security_docs tests.test_github_templates tests.test_code_of_conduct tests.test_project_files` | pass: 22 ran, 0 failed (exit 0). Log: `.../verify146/targeted-v.log` |
| Lint | not configured (`state.json` `commands.lint` is null) | not configured |
| Build | not configured (`commands.build` is null) | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass: `OK: 27 skills, 10 agents, 0 commands` (exit 0). Log: `.../verify146/validate.log` |
| Validate (pack) | `python3 scripts/brainrc.py validate --pack examples/pack-homelab` | pass: `OK: 27 skills, 10 agents, 0 commands (packs: homelab)` (exit 0). Log: `.../verify146/validate-pack-homelab.log` |
| Secret scan | `gitleaks git --redact --log-opts="main..HEAD" .` (8.24.3, checksum-verified binary, run by engine) | pass: 12 commits, no leaks |
| Plan / diff | `git diff main...HEAD -- . ':!specs'` | 14 files, +507/−2; offline only |

Scratchpad root: `/tmp/claude-0/-home-user/0dcec93d-71ed-51cf-87d5-99510717abc8/scratchpad/verify146/`. Raw output was kept there, not in `specs/<slug>/.runs/`, per the dispatch instruction. Working tree was clean at HEAD.

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | Files present: `CODE_OF_CONDUCT.md`, `SECURITY.md`, `GOVERNANCE.md`, `.github/CODEOWNERS`, `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/{bug_report.yml,feature_request.yml,config.yml}`. `test_files_exist` (security_docs, github_templates) pass. Community-profile percentage not readable offline: mapped to this file checklist only, per spec. | pass (checklist) |
| AC2 | `tests.test_security_docs.SecurityDocsTest.test_security_guard_model_and_links`, `test_security_private_reporting` pass | pass |
| AC3 | `test_security_docs ... test_security_supported_versions_and_response` passes | pass |
| AC4 | `tests.test_code_of_conduct` `test_is_contributor_covenant_2_1`, `test_enforcement_contact_is_private_report_url`, `test_no_email_address`, `test_has_enforcement_guidelines` pass. Text attributes Contributor Covenant 2.1 (line 117-119). | pass |
| AC5 | `tests.test_github_templates ... test_codeowners_owns_everything` passes. Manual: `.github/CODEOWNERS` = `* @bxker`. | pass |
| AC6 | `test_issue_forms_are_forms`, `test_config_disables_blank_issues_and_links_private_channel` pass. Manual: `config.yml` has `blank_issues_enabled: false` and a contact link to `/security/advisories/new`. | pass |
| AC7 | `test_github_templates ... test_pr_template_sections` passes | pass |
| AC8 | `tests.test_security_docs ... test_governance` passes | pass |
| AC9 | `tests.test_project_files ... test_privacy_statement`, `test_no_network_imports` pass. Privacy section added to README. Note: README wording also lists `git` (for packs by URL) and the configured eval command, not only `ccusage`. Code confirms `ccusage` only runs under `--ccusage` (`scripts/retro_report.py`, `scripts/retro_ccusage.py`). Literal AC9 wording is narrower than the README; flagged for reviewer. | pass (with note) |
| AC10 | `test_project_files ... test_readme_links_new_files`, `test_security_section_points_to_security_md` pass | pass |
| AC11 | `test_no_personal_data`, `test_no_personal_paths_or_emails`, `test_new_files_have_no_personal_data` pass. Manual grep of all added files for emails, `/Users/`, `/home/`, `/root/`, `.internal`, `.corp`: no matches. `validate` and unit tests pass. | pass |
| AC12 | `tests.test_project_files ... test_changelog_fragment` passes; `changelog.d/146-oss-project-files.md` added | pass |

## Notes
- No flakes observed in this run.
- The one skipped test in the full run was not identified; it is outside the new test set and was not investigated.
- `gitleaks` was not on the verifier's PATH; the engine ran the session's checksum-verified 8.24.3 binary over `main..HEAD`: no leaks.
- Repo settings (description, private vulnerability reporting) are out of scope per spec and are not verified.
- The change adds no new command or script, so no separate run-once was needed. Documented `validate` and test commands were run as written.
