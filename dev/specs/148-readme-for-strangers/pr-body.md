Lead the README with what brainrc syncs, plus a checked quickstart

3 of 4 in epic #113, stacked on #<PREV_PR>. Retarget to `main` before merging.

## Why
A first-time visitor landed on a README that led with spec-agent. Nothing said what brainrc syncs,
what `status` and `apply` print, or why to use it over chezmoi, stow, harness plugins, or rulesync.
A new user had to open docs/install.md to get a working apply.

## What changed
- The README opens with one config synced into Claude Code, Codex CLI, OpenCode, Antigravity CLI,
  and Cursor. Skills reach all five; rules, commands, agents, hooks, and MCP servers reach some
  (linked to harness support).
- Quickstart: clone, `status`, `apply`, `status`. It says the first `status` writes nothing and
  that `Everything in sync.` means the apply worked.
- Sample `status`/`apply` output from a real run in a temp HOME. It is abbreviated with `...`.
- "Why not …" table for chezmoi, GNU Stow, harness plugins, and rulesync, each linked, plus a row
  for brainrc's limits. One line points to ruler and dotagents.
- spec-agent moves below Install and the table. Its gates, `/work` example, and harness callout are unchanged.
- `scripts/check_tutorial.py --readme` runs the quickstart commands in a temp HOME and fails on a
  non-zero exit or a missing stable output line. CI runs it beside the tutorial step.

## Acceptance criteria
- [x] AC1: lead names the five enabled harnesses before spec-agent, verified by `tests.test_check_tutorial.RealReadmeTest.test_lead_precedes_spec_agent_and_names_five_tools`
- [x] AC2: skills-everywhere sentence and harness-support link in the lead, read in verify.md
- [x] AC3: `check_tutorial.py --readme` prints `PASS step 1 quickstart`; `test_real_readme_passes_and_stays_sandboxed`
- [x] AC4: `test_broken_command_fails`, `test_missing_documented_output_fails`
- [x] AC5: transcript present; `test_no_absolute_home_paths_or_emails`; grep for home paths, emails, hostnames is clean
- [x] AC6: four linked projects, no star counts, read in verify.md
- [x] AC7: cells cited to saved sources (chezmoi and Stow from GitHub READMEs). Not re-fetched in the offline run.
- [x] AC8: spec-agent section, three gates, `/work` example, callout unchanged; read in verify.md
- [x] AC9: README is 100 lines (`test_at_most_100_lines`); `tests.test_project_files` and `tests.test_plugin_docs` pass
- [x] AC10: `validate` OK (27 skills, 10 agents, 0 commands); unit suite 746 ran, 0 failed, 1 skipped (pre-existing); `check_tutorial.py` exit 0

## How to verify
```
python3 scripts/brainrc.py validate
python3 -m unittest discover -s tests
python3 scripts/check_tutorial.py
python3 scripts/check_tutorial.py --readme
```
The temp HOME isolates HOME-relative writes only. The README's shell commands are not sandboxed.
CI cells were not run locally: check the README step in the six blocking cells after push.

## Decisions made without you
- Gates auto-approved: Spec, Plan; see `specs/148-readme-for-strangers/log.md`
- Transcript is plain text from a real run, not an asciinema cast (open question 1).
- Table has rulesync only. Ruler and dotagents get one "also see" line (open question 2).
  dotagents links getsentry/dotagents, the closer match to its README. The research notes named a
  different Go package with that name. Owner to confirm.
- The quickstart check is `--readme` plus unit tests on one shared `run()` (open question 3).
- The check compares only stable lines, such as `Everything in sync.` (open question 4).
- Stow and chezmoi claims come from their GitHub READMEs; the project homepages returned 403 through the proxy.
- README is capped at 100 lines. The cap test fails on any addition.
- Ticket comment not posted: `specs/148-readme-for-strangers/ticket-comment.md`

## Follow-ups
- Asciinema cast of the quickstart.
- One sentence on CONFLICT for pre-existing unmanaged files (no line budget left).
- `check_tutorial.py` docstring should say the temp HOME is not a sandbox.
- A failing README step skips the later sandbox step in that CI cell (accepted).

Spec: `specs/148-readme-for-strangers/spec.md` · Plan: `specs/148-readme-for-strangers/plan.md`

Closes #148

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01Hn6pdU7RJ1sLQqc3fDP7Sa
