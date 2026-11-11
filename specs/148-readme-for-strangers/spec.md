# Spec: Rewrite the README for strangers

Ticket: gh:148 · Size: standard · Status: approved

## Problem
A first-time visitor lands on a README that leads with spec-agent, not with what brainrc is for
(one config synced into several AI tools). The install path is split across the README and
docs/install.md, there is no sample of what `status`/`apply` print, and nothing says why to use
brainrc instead of chezmoi, stow, harness plugins, or rulesync. The ticket's goal: a new user
reaches a working apply without opening another page.

## Goals
- README leads with the sync value proposition, then a short quickstart, sample output, and an honest comparison; spec-agent comes second.
- The quickstart cannot silently rot: its commands are run by a check.
- The README stays short enough to be a front page.

## Non-goals
- No change to brainrc behavior, harness support, or docs/install.md content beyond links.
- No asciinema recording or new tooling (follow-up, see Open questions).
- No star counts, benchmarks, or claims that another project "can't" do something undocumented.
- No rewrite of spec-agent.md, the harness-support caveat, Privacy/Security/Contributing sections.

## Acceptance criteria
- **AC1**: Given the README, when read top to bottom, then the first heading section states that one config is synced into Claude Code, Codex CLI, OpenCode, Antigravity CLI, and Cursor (the five enabled in `harnesses.toml`; retired Gemini not counted), before any mention of spec-agent.
- **AC2**: Given the lead section, when read, then it says that skills reach all five tools and that rules, commands, agents, hooks, and MCP servers reach only some, linking [harness support](docs/formats.md#harness-support).
- **AC3**: Given a machine with Python 3.11+ and git, when a user runs only the README quickstart commands (clone, `status`, `apply`), then both succeed with no other page opened, and the quickstart says how to confirm it worked and how `status` previews without writing.
- **AC4**: Given the quickstart commands in the README, when the test suite or CI runs, then those commands (with the clone replaced by a copy of the checkout, and HOME and BRAINRC_HOME in a temp dir) are executed and fail the build if any exits non-zero or the documented output changes. Stdlib only; the real HOME is never written.
- **AC5**: Given the README, when read, then it shows a plain-text transcript of `status` and `apply` output captured from a real local run, containing no absolute home paths other than `~`, no usernames, emails, or hostnames.
- **AC6**: Given the README, when read, then a "Why not ..." table compares brainrc with chezmoi, GNU stow, harness plugins/marketplaces, and rulesync, each name linked to its project page, and contains no star counts.
- **AC7**: Given each table cell about another project, when checked, then it states a capability stated in that project's own documentation, or says "not what it is for" without asserting inability. The table also states where brainrc is weaker (e.g. best on Claude Code, requires Python and a clone for non-Claude tools).
- **AC8**: Given the README, when read, then spec-agent follows the install and comparison sections, keeping the existing three-gate summary, the `/work` example, and the unequal-harness-support callout.
- **AC9**: Given the README, then it is at most 100 lines and keeps the existing Install, More, Contributing, Security, and Privacy content (links retained), and `tests/test_project_files.py` and `tests/test_plugin_docs.py` still pass (including `/plugin install brainrc@brainrc` present).
- **AC10**: Given the change, when `python3 scripts/brainrc.py validate`, the unit tests, and `python3 scripts/check_tutorial.py` run, then all pass.

## Constraints
Public repo: no secrets, personal emails, employer names, or absolute home paths. Examples use "acme". Python stdlib only. Every PR adds `changelog.d/<branch>.md`. docs/ pages may be edited only to fix links or duplication the README now covers.

## Requirement changes
### Area: project-docs
Purpose: The front-page README orients a new user and stays accurate.
#### ADDED: Runnable quickstart
The README SHALL contain a quickstart whose commands are executed by an automated check, and that check SHALL fail when a command fails or its documented output changes. (AC3, AC4)
#### ADDED: Fair comparison
The README SHALL compare brainrc with chezmoi, GNU stow, harness plugins, and rulesync using only documented, linked claims and SHALL state brainrc's limits. (AC6, AC7)

## Open questions
1. Asciinema: needs a tool outside the repo and a real-machine recording. *Matters because the ticket names it.* Default: ship the AC5 text transcript now; file the cast as a follow-up.
2. Include ruler or dotagents in the table? *Matters for fairness vs. length.* Default: no, rulesync only; link a one-line "also see ruler, dotagents" note.
3. Should the quickstart check live in `check_tutorial.py` (CI-only) or a unit test (runs locally)? *Matters for who sees breakage.* Default: unit test calling shared logic, left to the architect.
4. Sample output is machine-specific and will drift. *Matters for AC4.* Default: the check compares only stable lines (e.g. "Everything in sync."), not the whole transcript.
