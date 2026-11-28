# Plan: spec-agent `--auto` mode, no gate stops, draft PR(s) as output

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** a new `/work` flag `--auto` and a new `state.json` field `auto`
  (additive; runs without the flag are unchanged). Also a new exception in guardrails § Outward
  actions: `--auto` authorizes push plus a **draft** PR for the run's own branch (spec Q2).
- **Migrations / data changes:** none
- **Security triggers touched:** the gate and outward-action policy. Wording can't switch auto on
  (AC1), and every hard stop is kept (AC4). The security-reviewer reviews T1.
- **Domains:** scripting (tests), skill docs
- **Environments affected on deploy:** none; users get it on their next `aicfg apply` / plugin update
- **Destructive or replacing changes:** none

## Approach
Auto mode is engine text plus evals, with no aicfg code change. **T1** adds one `## Auto mode` section
to `skills/spec-agent/SKILL.md`, the file the engine reads every run, and points to it from § Run
steps 3–4 and § Deliver stage. Putting it there follows the e2e lesson that rules held only where the
engine reads them at that step. The section covers:
- `auto: true` is set at intake from `--auto` only.
- Each gate is still written (`lifecycle.md` § Gate presentation) to `log.md` as
  `## engine · <Gate> gate · auto-approved`, with both `metrics.gates` timestamps taken at that moment.
- Open questions take the analyst's stated default.
- The hard-stop list, with a pointer to `guardrails.md`.
- Deliver pushes and opens a draft PR. Ticket comments stay drafts (Q1). No merge, no base change, no issue close.
- In fallback mode the run doesn't stop for a fresh-session review. It records `review_context: shared` (Q3).
- `/spec-resume` resets `auto` unless `--auto` is given again.

`guardrails.md` gets an "Auto mode" row group in Stop conditions (size `large`, any Callout,
CRITICAL/HIGH security finding, untrusted-content instruction, a live target) and the one
outward-action exception. Smaller edits:
- `state.md`: the `auto` field.
- `templates/pr-body.md`: an optional `## Decisions made without you` section, auto only.
- `fallback.md` § Review isolation: one line for auto.
- `skills/work/SKILL.md`: the flag in `argument-hint` and the body, keeping "Stop at every gate" for non-auto runs.

**T2** adds `--auto` to `campaign.md` § Ordered shape. The Campaign gate and each child's Spec and Plan
gates are auto-approved, delivery is `stacked`, and the existing Failure rule pauses later children.
**T3/T4** add sandbox tickets and eval cases. Every check fits the existing kinds:
- `state`: `auto`, `blocked` present, `ticket.pr` absent.
- `file`: a `log.md` regex for `auto-approved`.
- `campaign`: with `delivery = "stacked"`.

So `scripts/evals.py` doesn't change. The sandbox has no remote, so "PR" means the branch recorded in `ticket.pr`.

Design choice: hard-stop evals cover the stops a ticket can plant (untrusted instruction, size
large, new dependency, secret, security finding) plus small and standard happy paths. Stops that
happen during a run (attempts > 2, scope breach, spec gap) can't be planted reliably by a ticket.
They use the same `state.blocked` path and are covered by the case shape, not a ticket each. This
narrows AC8. **Decide at the Plan gate.**

## Files
| File | Change |
|---|---|
| `skills/spec-agent/SKILL.md` | `## Auto mode`; pointers in § Run 3–4, § Deliver stage |
| `skills/spec-agent/references/guardrails.md` | auto stop conditions; outward exception |
| `skills/spec-agent/references/state.md` | `auto` field |
| `skills/spec-agent/references/fallback.md` | auto review-isolation line |
| `skills/spec-agent/templates/pr-body.md` | `## Decisions made without you` (auto only) |
| `skills/work/SKILL.md` | `--auto` flag |
| `skills/spec-agent/references/campaign.md` | auto campaigns |
| `examples/sandbox/tickets/011-017-*.md`, `examples/sandbox/README.md` | auto tickets |
| `evals/cases/sandbox-008.toml` … `sandbox-015.toml` | auto cases |
| `tests/test_evals.py` | case tests: each passes on a correct fake run and fails on a wrong one |

## Risks
- Generated plugin manifests may embed skill text (E1 finding): run `aicfg.py validate` per task and
  `aicfg.py plugin` if it reports them stale; add the manifests to that task's files.
- SKILL.md grows. Keep `## Auto mode` under ~25 lines and put detail in references.
- Evals grade text the engine writes; a model run is still needed for real evidence (docs/evals.md).

## Test strategy
`tests/test_evals.py`: one test class per new case (as `WatchRedCiCaseTest`). Each one writes a fake
run's `state.json`/`log.md` into a temp project, checks that `cmd_check` passes, then breaks one
field (e.g. sets `ticket.pr`, drops `blocked`, removes the `auto-approved` line) and checks that it
fails. Existing structure tests (cases name existing tickets, known kinds) cover the new files.
`aicfg.py validate` covers the skill frontmatter and links.

## Tasks
- [ ] **T1** [agent: implementer] Auto mode for single runs: engine rules, guardrails, state, PR template, `/work` flag
  - files: `skills/spec-agent/SKILL.md`, `skills/spec-agent/references/guardrails.md`, `skills/spec-agent/references/state.md`, `skills/spec-agent/references/fallback.md`, `skills/spec-agent/templates/pr-body.md`, `skills/work/SKILL.md`
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6
  - review: each
- [ ] **T2** [agent: implementer] Auto campaigns in `campaign.md`
  - files: `skills/spec-agent/references/campaign.md`
  - criteria: AC7
  - after: T1
- [ ] **T3** [agent: implementer] Sandbox tickets and eval cases for auto runs and hard stops
  - files: `examples/sandbox/tickets/`, `examples/sandbox/README.md`, `evals/cases/`, `tests/test_evals.py`
  - criteria: AC2, AC4, AC8
  - after: T1
- [ ] **T4** [agent: implementer] Auto campaign eval case
  - files: `evals/cases/`, `examples/sandbox/README.md`, `tests/test_evals.py`
  - criteria: AC7, AC8
  - after: T2, T3
