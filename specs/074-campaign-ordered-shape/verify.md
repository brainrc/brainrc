# Verify: Campaign ordered shape

Run at 2026-10-21T04:06:29Z on commit `8512a42`.

Raw output: `specs/074-campaign-ordered-shape/.runs/` (`test.log`, `validate.log`, `campaign-tests.log`, `campaign-fixtures.log`, `fixtures/`).

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 314 ran, OK, exit 0 (`.runs/test.log`) |
| Lint | none configured | not configured |
| Build | none configured | not configured |
| Validate (infra) | `python3 scripts/aicfg.py validate` | pass: `OK: 26 skills, 9 agents, 0 commands`, exit 0 (`.runs/validate.log`) |
| Targeted | `python3 -m unittest tests.test_evals.CampaignCheckTest -v` | pass: 8 ran, OK (`.runs/campaign-tests.log`) |
| Fixture, ordered run | `python3 scripts/evals.py check specs/074-campaign-ordered-shape/.runs/fixtures/ok evals/cases/sandbox-004.toml` | pass: 3 passed, 0 failed (campaign PASS, main_untouched PASS, command PASS) |
| Fixture, wrong order | same command on `.runs/fixtures/wrong-order` | fail as required: `FAIL campaign order [006, 005, 007], expected [005, 006, 007]`; exit 1 |
| Fixture, campaign only | `evals.py check <fixture> .runs/fixtures/campaign-only.toml` (ok: PASS, wrong-order: FAIL) | pass, as expected |

Fixtures are standalone git repos (`git init` plus one commit) copied from `examples/sandbox`. Members sit in epic child order (007, 005, 006). Member 005 is `order: 1`, `delivered`, with `pr` set. Members 006 and 007 are `waiting` with `pr: null`. All member `state.json` files have spec and plan `approved`. The wrong-order fixture swaps the `order` values of 005 and 006.

## Acceptance criteria
Engine behavior lives in markdown and is executed by an agent at run time. No ordered campaign has run yet, so every "read" result below was checked by reading the cited text. Only AC13 and AC18 have executable evidence (the eval check on fixtures).

| Criterion | Evidence | Result |
|---|---|---|
| AC1 | Read: detection rule `skills/spec-agent/references/campaign.md:35-40` (shared template and no links = playbook; links or differing members = ordered). Gate states shape and order: `campaign.md:62-63`. | pass (read) |
| AC2 | Read: `--shape` override `campaign.md:7`, `:39-40`; gate shows the used shape `:62-63`; `skills/work/SKILL.md:15` | pass (read) |
| AC3 | Read: Kahn topological sort, ties and unlinked children keep epic order, `campaign.md:122-123`. Not executed: the fixture encodes the expected order, it does not run the sort. | pass (read) |
| AC4 | Read: cycle or out-of-epic link stops at the Campaign gate and lists links, `campaign.md:122-125`. No test covers this. | pass (read) |
| AC5 | Read: `skills/ticket-local/SKILL.md:22` (`depends_on:` format) and `:45-51` (read-only `dependencies` returns refs); `skills/ticket-github/SKILL.md:54-68` (read-only op) | pass (read) |
| AC6 | Read: own `specs/<slug>/` and branch from N-1, `campaign.md:25-28`; active-run pointer names child in progress, `campaign.md:130`, `skills/spec-agent/references/state.md:123-136`. Not checked: `active_run.py` itself (not in the changed set). | pass (read) |
| AC7 | Read: one Deliver gate listing every child's outward actions verbatim in merge order, `campaign.md:132-133` | pass (read) |
| AC8 | Read: after approval only `order: 1` is `delivered` with `pr` set; others `waiting`, `pr: null`, `campaign.md:134-135`. Fixture `.runs/fixtures/ok` has this state and the campaign check passes. | pass (read) + fixture |
| AC9 | Read: release merges `main`, re-runs tests, opens PR with "N of M, after #X" and epic link, `campaign.md:137-139` | pass (read) |
| AC10 | Read: earlier-PR review change merged into later branches and tests re-run, `campaign.md:139-141` | pass (read) |
| AC11 | Read: failed or blocked child pauses later children only, `campaign.md:143-144` | pass (read) |
| AC12 | Read: `campaign.json` schema (`shape`, `order`, `depends_on`, `waiting`), `campaign.md:27-29` and `:112-117`; `## Ordered shape` marked skippable, `campaign.md:103-105`; resume, `state.md:146-150`. Fixture `campaign.json` matches the schema. | pass (read) + fixture |
| AC13 | `evals/cases/sandbox-004.toml`; tickets `examples/sandbox/tickets/004-greeting-epic.md` (children 007, 005, 006), `006` depends on `005`, `007` depends on `006`. Fixture `ok`: PASS campaign (order, gates, only first delivered). | pass (fixture + read) |
| AC14 | Read: `docs/spec-agent.md:51-56` describes both shapes | pass (read) |
| AC15 | Read: pull-based merge check on resume, release only if merged or user says "merged", no polling: `campaign.md:146-149`; `state.md:146-150`; `skills/spec-agent/SKILL.md:74-76`; `skills/work/SKILL.md:16-17`. `grep -rn poll` finds only "never polled" wording. | pass (read) |
| AC16 | Read: `ticket-github` uses `gh api .../dependencies/blocked_by`, falls back to `^Depends on #(\d+)` body lines, `skills/ticket-github/SKILL.md:54-68`; gate states source, `campaign.md:62-63`, `:119` | pass (read) |
| AC17 | Read: `--shape ordered` with no links uses sub-issue order, stated at gate, `campaign.md:39-40`, `:62-63`, `:122` | pass (read) |
| AC18 | `scripts/evals.py:25`, `:96-115` (`_campaign`), `:165-166` (dispatch), `:170-193` (`cmd_check` finds campaign). `tests/test_evals.py:211-296` (`CampaignCheckTest`, 8 tests pass): good campaign passes; wrong order, unapproved plan gate, second member delivered, first member without PR, and waiting-with-delivered status all fail. Fixture `wrong-order` fails on order. | pass |

## Notes
- Read-only results (AC1-AC12, AC14-AC17) are checked against the docs text only. They are not run, so they are not proven to hold when an agent executes them. The spec's Notes say the same.
- A first fixture attempt placed the copy inside this repo without its own `.git`. `main_untouched` then counted 339 commits of the outer repo and failed. That was a fixture-location artifact, not a defect. The reported results use standalone fixture repos.
- `command` check in the sandbox case runs the sandbox's own `greet` tests, which are the unmodified initial code. It shows the harness runs, not that the 005-007 features work.
- No flaky failures were seen; no test was re-run.
- Nothing in the repo was edited, except `specs/074-campaign-ordered-shape/verify.md` and `.runs/`.
