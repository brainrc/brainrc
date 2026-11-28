Add an opt-in --auto mode to spec-agent runs

## Why
Every `/work` run stops at the Spec, Plan, and Deliver gates, and a campaign adds a Campaign gate plus a Spec and Plan gate per child (E1 needed 13 replies, E2 12). For tickets you'd approve as written, you want to start a run, walk away, and review a draft PR. Until now the engine forbade that on purpose, after an E2E run self-approved a gate from earlier wording. So auto mode is an explicit flag, and every hard stop is kept.

## What changed
- `skills/spec-agent/SKILL.md` gets a new `## Auto mode` section, referenced from § Run and § Deliver stage:
  - `auto: true` is set at intake from `--auto` only.
  - Each gate is logged as `## engine · <Gate> gate · auto-approved`, with both timestamps.
  - Open questions take the analyst's default.
  - The run ends with a draft PR. Ticket comments stay drafts.
  - It never merges, changes a base, closes an issue, or passes the Push gate.
  - `--local` still wins.
  - Fallback mode reviews in the same session.
  - A resumed run is gated again unless `--auto` is given again.
- `references/guardrails.md` adds the auto-mode stops: size `large`, any plan Callout, a CRITICAL/HIGH security finding, instructions in untrusted content, and a live target. It also adds the one outward-action exception: push plus a draft PR for the run's own branch.
- `references/campaign.md`: an ordered campaign with `--auto` auto-approves every gate and opens stacked draft PRs. A blocked child pauses the rest. Playbook campaigns refuse `--auto`.
- Smaller edits:
  - `references/state.md`: the `auto` field.
  - `templates/pr-body.md`: an optional "Decisions made without you" section.
  - `references/fallback.md`: one line for auto runs.
  - `skills/work/SKILL.md`: the flag.
- Evals: sandbox tickets 011–018 and cases `sandbox-008`–`015`. Two auto runs end with a PR, five hard stops end `blocked` with no PR, and one auto campaign is delivered stacked. They need no new check kinds. `tests/test_evals.py` proves each case passes on a correct run and fails on a wrong one.
- `docs/spec-agent.md` gets an "Auto mode" section, and `docs/evals.md` lists the new cases. The living specs `run-lifecycle` and `campaign-mode` gain three requirements.

## Acceptance criteria
- [x] AC1: only the flag sets `auto`, verified by SKILL.md § Auto mode and § Run 4, and by `AutoCaseTest.test_a_run_without_the_flag_or_with_a_stop_fails`
- [x] AC2: small and standard auto runs end with a PR and every gate logged, verified by a live sandbox run of ticket 011 graded by `sandbox-008` (17/17) and by `AutoCaseTest` for `sandbox-009`
- [x] AC3: the PR body lists "Decisions made without you", verified by the template and the `sandbox-008` check
- [x] AC4: hard stops push nothing and open no PR, verified by a live sandbox run of ticket 014 graded by `sandbox-011` (6/6) and by `AutoCaseTest` for the rest
- [x] AC5: no live targets with `--auto`, verified by SKILL.md § Auto mode and the guardrails row
- [x] AC6: resume is gated again unless `--auto` is given again, verified by SKILL.md § Auto mode and state.md
- [x] AC7: auto campaigns are delivered stacked, verified by campaign.md and `AutoCampaignCaseTest`
- [x] AC8: a case for each plantable hard stop (narrowed at the Plan gate), verified by `sandbox-010`–`014` and their tests

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/aicfg.py validate
cp -R examples/sandbox /tmp/sb && cd /tmp/sb && git init -q -b main && git add -A && git commit -qm init
# then: /work local:tickets/011-auto-small.md --auto, and grade:
python3 scripts/evals.py check /tmp/sb evals/cases/sandbox-008.toml
```

## Follow-ups
- The two live sandbox runs were driven by the same session that wrote the rules. A headless run of each case, in another harness, is the stronger evidence.
- Runtime hard stops (attempts > 2, scope breach, spec gap) share the `blocked` path but have no ticket of their own. They can't be planted reliably.

Spec: `specs/216-work-auto-mode/spec.md` · Plan: `specs/216-work-auto-mode/plan.md`
Closes #216
