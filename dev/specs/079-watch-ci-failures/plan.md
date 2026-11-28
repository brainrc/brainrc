# Plan: watch 2/4: `watch` stage for CI failures, with a Push gate

Spec: [spec.md](spec.md) · Status: draft

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** additive `state.json` schema (`stage: watch`, `gates.push`, `watch.{checked_at,head_sha,ci_failures[]}`, `metrics.post_deliver_retries`, `gate_rework.push`); env var `SPEC_PR_STATUS_FIXTURE`; fixture log convention `<fixture-stem>.<check>.log`; eval `state` fields accept numeric index segments.
- **Migrations / data changes:** none (old runs lack `watch`; absent means not watched)
- **Security triggers touched:** outward-action gating (new Push gate in guardrails), untrusted input (CI logs, PR data)
- **Domains:** scripting
- **Environments affected on deploy:** none (docs, skill text, offline eval)
- **Destructive or replacing changes:** none

## Approach
A new `skills/spec-agent/references/watch.md` holds the whole procedure, sections `## Enter`, `## Fixture hook`, `## Resume pass`, `## CI failure`, `## Push gate`. SKILL.md § Deliver stage step 3, `lifecycle.md`, `guardrails.md`, `state.md` § Resume and `work/SKILL.md` get short pointers. **Enter:** after `link_pr`, with `delivery: normal` and the connector's `pr_status` heading (`connectors.md`) or the fixture hook set, deliver writes `retro.md` as today, then sets `stage: watch`, `watch.checked_at`, and records `head_sha`. Otherwise `done`, with no `watch` key. **Resume pass:** one `pr_status` read. If `updated_at <= checked_at` and `head_sha` is unchanged, report "no change" and touch nothing else. `merged`/`closed` are reported only (#81) and threads are left alone (#80). No loops.
**CI failure:** per `failure` check not already in `ci_failures` for this sha: summarize its log to `.runs/watch-<check>-<sha7>.md` (efficiency.md; raw log in `.runs/` only, fenced as untrusted). GitHub reads it with `gh pr checks --json name,link` + `gh run view <id> --log-failed`. Base red comes from read-only `gh api .../commits/<base>/check-runs`; under the fixture it is unknown, treated as not red. Next, match paths in the log exactly against `git diff <base>...HEAD --name-only`. Red on base or no match → `cause: external`, no task, a one-line note, stop. Match → `cause: own`, `task: C<n>`, and a `tasks[]` entry (implementer, files = matched paths, `review: each`) run through SKILL.md's per-task loop (attempts > 2 stops). Creation and each retry add +1 to `metrics.post_deliver_retries` (not `metrics.retries`, so pre-deliver numbers stay comparable). An unreadable log blocks; it is never guessed `external`.
**Push gate:** `gates.push` resets to `pending` per push. The gate message (lifecycle shape) shows `git diff --stat` and `git log --oneline` for the unpushed commits plus the check it fixes. `metrics.gates.push` and `gate_rework.push` follow existing gate rules. Push only on approval. On rejection or silence, stay at `watch` and keep the commits local. **Fixture hook:** when `SPEC_PR_STATUS_FIXTURE` names a file, read `pr_status` from it, treat the connector as supporting it, and read check logs from the sibling `<stem>.<check>.log`. Nothing else changes. That lets a no-remote sandbox run (`delivery: normal`, ticket-local records the branch, no push possible) reach `watch` offline. **Eval:** `_field` in `scripts/evals.py` indexes lists on digit segments, out of range → `None`.

## Files
| File | Change |
|---|---|
| `scripts/evals.py`, `tests/test_evals.py`, `docs/evals.md` | modify: numeric index in `_field`; tests; doc row |
| `skills/spec-agent/references/watch.md` | new: procedure above |
| `skills/spec-agent/SKILL.md`, `references/lifecycle.md`, `references/guardrails.md`, `skills/work/SKILL.md` | modify: pointers, stage row, Push gate as allowed outward action, CI logs untrusted |
| `skills/spec-agent/references/state.md` | modify: schema, field table, rules, Resume at `watch` |
| `docs/post-deliver.md`, `docs/spec-agent.md`, `changelog.d/079-watch-ci-failures.md` | modify/new: status line, stage summary, fragment |
| `examples/sandbox/tickets/008-watch-red-ci.md`, `examples/sandbox/pr_status/red-ci.unit-tests.log`, `examples/sandbox/README.md`, `evals/cases/sandbox-005.toml` | new/modify: red-CI eval |

## Risks
- A full sandbox run can't truly fix a fake CI failure, so per resolved Q6 the grading is proven on a synthetic run folder.
- Guardrails wording could open push outside gates. Mitigated by `review: each` on T2 and T3.
- `retro_metrics.STAGES` ignores `watch`, so its rollup comes in #81. Unknown stages are already skipped.

## Test strategy
Unit (`tests/test_evals.py`): numeric index pass and fail (AC10). `sandbox-005` grades a synthetic watch run folder: it passes on good state, and fails on `cause: external`, on `gates.push: approved`, and on a commit on main (AC9). A fixture test checks that the log names a file the ticket changes. Doc ACs (AC1–AC8) are checked by review and the verifier against the text. `validate` plus the full suite run in verify.

## Tasks
- [ ] **T1** [agent: implementer] Numeric index segments in eval `state` checks (test-first)
  - files: `scripts/evals.py`, `tests/test_evals.py`, `docs/evals.md`
  - criteria: AC10 · wave 1
- [ ] **T2** [agent: implementer] `references/watch.md`: enter, fixture hook, resume pass, CI triage, C-tasks, Push gate
  - files: `skills/spec-agent/references/watch.md`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7 · review: each · wave 1
- [ ] **T3** [agent: implementer] `state.md` schema and Resume at `watch`
  - files: `skills/spec-agent/references/state.md`
  - criteria: AC3, AC6, AC8 · wave 1
- [ ] **T4** [agent: implementer] Wire pointers: SKILL.md deliver step, lifecycle row and Push gate, guardrails, /work
  - files: `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/lifecycle.md`, `skills/spec-agent/references/guardrails.md`, `skills/work/SKILL.md`
  - criteria: AC1, AC2, AC7, AC8 · review: each · after: T2 · wave 2
- [ ] **T5** [agent: implementer] Docs status and changelog fragment (`bump: patch`)
  - files: `docs/post-deliver.md`, `docs/spec-agent.md`, `changelog.d/079-watch-ci-failures.md`
  - criteria: AC8 · after: T2 · wave 2
- [ ] **T6** [agent: implementer] Red-CI sandbox eval: ticket 008, log fixture, `sandbox-005.toml`, README setup, synthetic-run grading tests
  - files: `examples/sandbox/tickets/008-watch-red-ci.md`, `examples/sandbox/pr_status/red-ci.unit-tests.log`, `examples/sandbox/README.md`, `evals/cases/sandbox-005.toml`, `tests/test_evals.py`, `docs/evals.md`
  - criteria: AC4, AC9, AC10 · after: T1 · wave 2
  - Case checks: `stage`=watch, `watch.ci_failures.0.cause`=own, `.0.task`=C1, `gates.push`=pending, `main_untouched`, `command git remote` stdout "" (no push target), `file {spec}/.runs/watch-unit-tests-3f2a9c1.md` matches `test_greet\.py`. README: `SPEC_PR_STATUS_FIXTURE=$PWD/pr_status/red-ci.json`, run 008 through Deliver, stop at the Push gate.
