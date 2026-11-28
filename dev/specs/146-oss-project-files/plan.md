# Plan: Open-source project files

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** none (docs only; SECURITY.md describes the existing guard model)
- **Domains:** none (docs, stdlib unittest)
- **Environments affected on deploy:** none. Owner follow-ups for the PR body: enable private vulnerability reporting, set the repo description.
- **Destructive or replacing changes:** none

## Approach
Markdown and YAML files only. SECURITY.md summarizes and links `docs/guardrails.md` (layers table,
"Known gaps") rather than restating it. Reports for security and conduct go to GitHub private
vulnerability reporting (`https://github.com/brainrc/brainrc/security/advisories/new`), Q1 default.
Issue templates are YAML forms with `blank_issues_enabled: false` and a `contact_links` entry for
that URL (Q4). Supported versions: latest release only (Q3). GOVERNANCE restates CONTRIBUTING's
squash-merge and CI flow and links it rather than copying it.

The no-telemetry statement is a short `## Privacy` section in README. It is verified against code:
`brainrc/`, `scripts/`, and `overrides/*/hooks` import no `urllib`/`http.client`/`socket`/`requests`.
The only subprocesses are `git` (`brainrc/packs.py`, only for packs the user configures), hook
self-tests (`brainrc/doctor.py`), and `ccusage` under `--ccusage` (`scripts/retro_ccusage.py`). The
wording must cover `git` so the claim stays true (see Risks).

Tests follow `tests/test_plugin_docs.py` (`ROOT`, `text(rel)`, plain `unittest`). There is one test
file per task, so tasks T1 to T3 share no files and can run in parallel. T4 owns the README and the
check across all files.

## Files
| File | Change |
|---|---|
| `SECURITY.md`, `GOVERNANCE.md`, `CODE_OF_CONDUCT.md` | new |
| `.github/CODEOWNERS`, `.github/pull_request_template.md` | new |
| `.github/ISSUE_TEMPLATE/{bug_report.yml,feature_request.yml,config.yml}` | new |
| `README.md` | modify: More-table rows, Privacy section, Security points to SECURITY.md |
| `tests/test_security_docs.py`, `tests/test_github_templates.py`, `tests/test_code_of_conduct.py`, `tests/test_project_files.py` | new |
| `changelog.d/146-oss-project-files.md` | new, `bump: patch` |

## Risks
- AC9 says ccusage is the "only external command", but `git` also runs for packs. The README wording names both, and the T4 test pins that there are no network imports.
- The reporting link dead-ends until the owner enables the setting. This is listed as a PR-body follow-up.
- Covenant text drifts from upstream. Use the 2.1 text verbatim, with attribution and its URL.

## Test strategy
Unit tests (stdlib) pin presence and key content per AC, written first in each task. Manual: AC1 checklist against the community-profile items. Run `validate` and the full suite each task.

## Tasks
- [ ] **T1** [agent: implementer] SECURITY and GOVERNANCE
  - files: `SECURITY.md`, `GOVERNANCE.md`, `tests/test_security_docs.py`
  - criteria: AC1, AC2, AC3, AC8, AC11. Tests: SECURITY links `docs/guardrails.md`, names "Report a vulnerability" and the advisories URL, says not to use public issues, has a supported-versions section, has no "within N hours/days". GOVERNANCE names maintainer `bxker`, squash-merge, CI, and a path to maintainer.
- [ ] **T2** [agent: implementer] CODEOWNERS, PR template, issue forms
  - files: `.github/CODEOWNERS`, `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml`, `tests/test_github_templates.py`
  - criteria: AC1, AC5, AC6, AC7, AC11. Tests: CODEOWNERS non-comment lines are `* @bxker`. config has `blank_issues_enabled: false` and a contact link to the advisories URL. Both forms have `name:` and `body:`. The PR template has Why, What changed, How to verify, `Closes #`, `changelog.d/`, and both check commands. No YAML lib, so use string checks.
- [ ] **T3** [agent: implementer] Contributor Covenant 2.1
  - files: `CODE_OF_CONDUCT.md`, `tests/test_code_of_conduct.py`
  - criteria: AC1, AC4, AC11. Tests: has "Contributor Covenant" and "version 2.1" with the attribution URL, the enforcement contact is the advisories URL, and there is no `@` email.
- [ ] **T4** [agent: implementer] README links, Privacy statement, hygiene test, changelog
  - files: `README.md`, `tests/test_project_files.py`, `changelog.d/146-oss-project-files.md`
  - criteria: AC9, AC10, AC11, AC12. Tests: README links all new files, Security section links `SECURITY.md`, and Privacy mentions `--ccusage`. No email regex, `/Users/`, or `/home/` match in any new file. `brainrc/`, `scripts/`, and `overrides/` import no network modules.
  - after: T1, T2, T3
