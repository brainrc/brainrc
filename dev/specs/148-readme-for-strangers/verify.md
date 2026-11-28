# Verify: Rewrite the README for strangers

Run at 2026-11-03T13:17:24Z on commit `b226a93`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 746 ran, 0 failed, 1 skipped (pre-existing skip). Log: `/tmp/claude-0/-home-user/0dcec93d-71ed-51cf-87d5-99510717abc8/scratchpad/verify148/test.log` |
| Targeted tests | `python3 -m unittest tests.test_project_files tests.test_plugin_docs -v` | pass: 11 ran, 0 failed (`targeted.log`) |
| New tests (verbose) | `python3 -m unittest tests.test_check_tutorial -v` | pass: 24 ran, 0 failed (`new-tests.log`) |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate | `python3 scripts/brainrc.py validate` | pass: `OK: 27 skills, 10 agents, 0 commands` (`validate.log`) |
| Tutorial | `python3 scripts/check_tutorial.py` | pass: steps 1-5 PASS, exit 0 (`tutorial.log`) |
| README quickstart | `python3 scripts/check_tutorial.py --readme` | pass: `PASS step 1 quickstart`, exit 0 (`readme-check.log`) |
| Secrets | `gitleaks git --redact --log-opts=147-ci-matrix..HEAD` | pass: 10 commits scanned, no leaks (`gitleaks.log`, `gitleaks.json`) |
| Plan / diff | n/a | offline only |

All raw output is under `/tmp/claude-0/-home-user/0dcec93d-71ed-51cf-87d5-99510717abc8/scratchpad/verify148/`.

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `tests.test_check_tutorial.RealReadmeTest.test_lead_precedes_spec_agent_and_names_five_tools` ok. Read README: lead (lines 1-4) names Claude Code, Codex CLI, OpenCode, Antigravity CLI, Cursor before `## spec-agent`. Gemini not mentioned. | pass |
| AC2 | Same lead paragraph: "Skills reach all five tools. Rules, commands, agents, hooks, and MCP servers reach only some ... ([harness support](docs/formats.md#harness-support))." | pass |
| AC3 | Ran `check_tutorial.py --readme` (clone replaced by a checkout copy, temp HOME): `PASS step 1 quickstart`. Quickstart text says the first `status` writes nothing and `Everything in sync.` confirms success. Tests `test_quickstart_commands_are_status_apply_status`, `test_fixture_passes`, `test_real_readme_passes_and_stays_sandboxed` ok. | pass |
| AC4 | `check_tutorial.py --readme` runs the quickstart commands. Fails on non-zero exit or missing documented stable output: `test_broken_command_fails`, `test_missing_documented_output_fails`, `test_missing_section_is_a_fail_line` ok. Runs inside the unit suite (746 OK). Stdlib only, HOME sandboxed. CI step is in `.github/workflows/validate.yml` per T1; CI cell not run locally (see Notes). | pass |
| AC5 | README transcript present under Quickstart. `test_no_absolute_home_paths_or_emails` ok. My grep for `/home/`, `/Users/`, `/root/`, email, and hostname patterns: no match. Only host reference is `https://github.com/brainrc/brainrc` and the `~/brainrc` clone path. Transcript captured from a temp-HOME run per log.md T2 and code-reviewer evidence. It is abbreviated with `...` (see Notes). | pass |
| AC6 | "Why not …" table lists chezmoi, GNU Stow, Harness plugins, rulesync, each linked. No star counts. `test_expected_output_is_shown_in_the_readme` and README read. | pass |
| AC7 | Per-cell sources recorded in log.md, T3 block: chezmoi and Stow from GitHub READMEs (homepages returned 403 via proxy), plugins from code.claude.com/docs/en/plugins, rulesync and ruler/dotagents from their READMEs. Code-reviewer block: "'Why not' cells match their saved sources." Brainrc limits row present (best on Claude Code; Codex, Antigravity, Cursor best effort; needs Python 3.11+ and a clone). Verifier did not re-fetch external sources (offline run). | pass (cited) |
| AC8 | README: spec-agent section follows Install and Why-not; three-gate summary (spec, plan, delivery); `/work gh:42` example; harness-support callout block present. | pass |
| AC9 | README is 100 lines (`wc -l`; `test_at_most_100_lines` ok). Install, More, Contributing, Security, Privacy sections present with links. `tests.test_project_files` and `tests.test_plugin_docs` ok. `/plugin install brainrc@brainrc` present. | pass |
| AC10 | `validate` exit 0; `check_tutorial.py` exit 0; full unit suite 746 OK. | pass |

## Notes
- AC5 transcript is abbreviated: it elides middle lines with `...` and "(about 160 lines, one per file)". The spec asks for a transcript "captured from a real local run" and the check compares only stable lines, so this is accepted, but a reviewer should know the README text is not a verbatim dump.
- Verify-after-push: the CI cells of `.github/workflows/validate.yml` (T1 step) were not run. Re-check after push.
- Review findings (non-blocking, accepted or filed as follow-ups):
  - infra-reviewer LOW: a failing README step skips the later sandbox step in that CI cell. Accepted.
  - infra-reviewer LOW: temp HOME isolates HOME-relative writes only; README bash is not sandboxed. Follow-up (docstring wording).
  - code-reviewer LOW: rulesync row wording could read as "no hooks". Fixed in engine.
  - code-reviewer LOW: 100-line cap test trips on any addition. Accepted (spec cap).
  - code-reviewer LOW: quickstart does not mention CONFLICT for pre-existing unmanaged files. Follow-up.
- dotagents link points to getsentry/dotagents (closer match per T3 notes).
- No check was skipped. No flaky failures observed.
