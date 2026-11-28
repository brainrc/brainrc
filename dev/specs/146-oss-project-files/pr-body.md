Add open-source project files and a Privacy section

1 of 4 in epic #113.

## Why
The repo is public but had no code of conduct, security policy, issue or PR templates,
CODEOWNERS, or governance text. A reader could not tell how to report a guard bypass privately,
or whether brainrc sends data anywhere.

## What changed
- `SECURITY.md`: the guard model (hooks are a seatbelt, credentials are the boundary), what to
  report and what counts as a known gap, private reporting through the Security tab, the
  supported version (latest release only), and the expected response.
- `CODE_OF_CONDUCT.md`: Contributor Covenant 2.1, attributed. Reports go to the private channel.
- `GOVERNANCE.md`: the maintainer decides, changes land by PR with squash-merge after CI is green,
  and how a contributor becomes a maintainer.
- `.github/CODEOWNERS` (`* @bxker`), a PR template, and YAML issue forms for bugs and features.
  Blank issues are off, and `config.yml` points security reports to the private channel.
- README: links the new files, points the Security section to `SECURITY.md`, and adds a Privacy
  section.
- `changelog.d/146-oss-project-files.md` (patch).

## Acceptance criteria
- [x] AC1-AC3, AC8: required files exist with the required content (`tests.test_security_docs`)
- [x] AC4, AC5-AC7: Covenant text, CODEOWNERS, issue forms, and PR template (`tests.test_code_of_conduct`, `tests.test_github_templates`)
- [x] AC9: Privacy statement (`tests.test_project_files`). Wording is broader than AC9; see Decisions.
- [x] AC10-AC12: README links, no personal data, changelog fragment (`tests.test_project_files`)

## How to verify
```
python3 scripts/brainrc.py validate
python3 -m unittest discover -s tests
```
On `c41a116`: 725 tests OK, 1 skipped. Docs only. No runtime code, hooks, or dependencies changed.
Rollback: revert the PR. The community profile score is not checked offline; compare the checklist
after merge and the owner's settings follow-ups.

## Decisions made without you
- Gates auto-approved: Spec and Plan; Deliver is expected at the stack gate. See `specs/146-oss-project-files/log.md`.
- Q1: GitHub private vulnerability reporting is the only contact for security and conduct reports. No email is committed.
- Q2: repo description and settings are follow-ups, not part of this PR.
- Q3: only the latest release is supported.
- Q4: YAML issue forms, blank issues off.
- AC9: the Privacy statement also names `git` (packs fetched by URL) and the eval scripts' configured command. Only `ccusage` (opt-in, `--ccusage`) is named in AC9. The README wording is accurate.
- Ticket comment not posted: `specs/146-oss-project-files/ticket-comment.md`.

## Follow-ups
- Owner enables private vulnerability reporting (Settings → Code security). Until then the report links dead-end.
- Owner sets the repo description.
- LOW: the network-import test matches line-start imports only. Accepted as a smoke test.

Spec: `specs/146-oss-project-files/spec.md` · Plan: `specs/146-oss-project-files/plan.md`

Closes #146

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01Hn6pdU7RJ1sLQqc3fDP7Sa
