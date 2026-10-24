# Lifecycle

Stages run in this order. [sizing.md](sizing.md) decides which ones run.
`state.json` → `stage` always names the stage in progress.

| # | Stage | Actor | Reads | Writes | Exit |
|---|---|---|---|---|---|
| 0 | `intake` | engine | ticket (via connector) | `ticket.md`, `state.json`, branch | size stated, commands discovered |
| 1 | `spec` | analyst | `ticket.md`, `specs/living/`, code | `spec.md` | ⛔ **Spec gate** approved |
| 2 | `plan` | architect | `spec.md`, code | `plan.md` (incl. tasks), `state.tasks` | ⛔ **Plan gate** approved |
| 3 | `implement` | implementer (or test-writer) per task, then batched review | `plan.md`, `spec.md` | code, tests, one commit per task | every task `done`, review clean |
| 4 | `verify` | verifier | `spec.md`, `state.commands` | `verify.md` | every criterion `pass` with evidence |
| 5 | `document` | engine, doc-writer | all artifacts, diff | `specs/living/`, project docs, `pr-body.md`, `ticket-comment.md` | drafts exist |
| 6 | `deliver` | engine, examiner, ticket connector | drafts, diff | quiz rounds in `log.md`, then push, PR, ticket comment/status | quiz passed, then ⛔ **Deliver gate** approved before *any* outward action |
| 7 | `done` | engine | `state.metrics` | `retro.md` | retro written |

`blocked` is not a stage. It is `state.blocked`, set by any stop condition
([guardrails.md](guardrails.md)). The stage is kept so resume knows where to continue.

## Stage details

**0 · intake**
1. Check `git status`. If the working tree is dirty, stop and ask. (Check first: the next
   steps create files, and those are the engine's own.)
2. Parse the ticket reference: `gh:<n>`, a GitHub issue URL, `jira:<KEY-n>` or a Jira browse
   URL (ticket-jira), `local:<path>`, or free text
   (free text becomes a local ticket at `specs/tickets/<NNN>-<slug>.md`, see ticket-local).
   A ref that matches a pack connector's `refs` (`extensions.md`, SKILL.md § Packs) uses that connector.
3. If the repo has a `VERSION` file and no `changelog.d/` (fragments don't conflict), list other open PRs that change `VERSION` or `CHANGELOG.md`
   (through the connector's system, e.g. `gh pr list` or its MCP equivalent). If any exist,
   name them and recommend waiting for them to merge before branching, since both will claim
   the same next version. Can't list PRs → say so in one line and continue.
4. Create the branch `<slug>` from the default branch (or check it out if it exists → resume).
5. Fetch the ticket through the connector skill and write `ticket.md` (format in
   [state.md](state.md)). Run any pack Intake context skills and append their summaries.
   Files written during intake go into the first checkpoint commit. Record the run as active
   (`python3 <skill>/scripts/active_run.py write <project root>/specs/<slug>`, state.md § Active run pointer).
6. Discover project commands with the [project-commands](../../project-commands/SKILL.md) skill.
7. Detect domains (see the Domains table in SKILL.md). If evidence needs a live environment,
   ask which targets are allowed ([guardrails.md](guardrails.md) § Environments).
8. Classify size ([sizing.md](sizing.md)) and say it in one line with the mode. The user may
   override. If the harness can run subagents but the named agents aren't installed (Claude
   Code without `~/.claude/agents/analyst.md`), say it runs in `fallback` and that
   `python3 scripts/aicfg.py apply` in ai-config installs them.
9. Set `delivery`: `local-only` when the user asks for it (`--local`, "don't open a PR", working on
   someone else's repo without push rights), else `normal`. Record it in state.

**1 · spec**: the analyst turns the ticket into testable acceptance criteria and lists
open questions, and states the requirement delta against the living specs it read (new behavior with no living
area creates one). Before the gate, run `python3 <skill>/scripts/living_specs.py check
specs/<slug>/spec.md` and have the analyst fix any error, so the delta that gets approved is the
one that applies. At the gate, show the criteria and questions. If the user answers questions, the analyst revises (count
one `gate_rework.spec` per revision round).

**2 · plan**: the architect writes the approach and the task list. Each task names its
agent, the files it may touch, and the criteria it satisfies. Any new dependency or
public API change must be called out at the top of `plan.md`.

**3 · implement**: loop over tasks in order (see the per-task loop in [SKILL.md](../SKILL.md)).

**4 · verify**: run the full test, lint, build, and validate commands (and plan/diff against
approved targets). Map every acceptance criterion to
evidence in `verify.md`, written from `templates/verify.md`: its `## Checks` and
`## Acceptance criteria` sections, criteria columns `Criterion | Evidence | Result`. Any `fail` → back to `implement` with a new fix task (counts as a retry).

**5 · document**: first apply the spec's delta to the living specs:
`python3 <skill>/scripts/living_specs.py apply specs/<slug>/spec.md` (`check` first if unsure).
It writes nothing when any block is wrong; fix `spec.md` (a change to the approved spec, so say
so at the Deliver gate) and re-run. Record the areas in `state.living` and commit them with the
docs. Without Python, the doc-writer applies the delta by hand with the same rules. Then update
docs the change affects (README, CHANGELOG, API docs) and draft outward text. Nothing is posted.

**6 · deliver**: re-run the intake `VERSION` check. If such a PR merged meanwhile, merge the
default branch and renumber this run's version before the gate. Run the Understand quiz (below), then
show the Deliver gate summary (below). Only after approval: push the
branch, open the PR, comment on / transition the ticket, and link the PR.
With `delivery: local-only`, the gate lists **no outward actions**: deliver finalizes the drafts
(`PR: <PR_URL>` → `PR: none (local-only, branch <branch>)`), leaves the branch unpushed, and
writes the retro.

**7 · done**: write `retro.md`, print the PR link and the metrics summary. Commit the done
checkpoint, but push it only after CI on the delivered commit finishes: a push while CI runs
can break steps that list the PR's commits.

## Understand quiz

The owner (the person who started the run) shows they understand the change before the Deliver
gate opens. Every size runs it. An unattended run stops here and the quiz waits for the owner.
There is no skip.

1. Write `git diff <base>...HEAD -- . ':!specs'` to `.runs/deliver-diff.patch`. Dispatch
   `examiner` with `Read:` spec.md, plan.md, verify.md, that patch, and the review findings, plus
   a `Size:` line and a `Triggers:` line naming any security, IAM, migration, or prod trigger the
   diff touches. Count: trivial 1, small 2, standard 3–5, +1 `risk` per trigger.
2. Check the handoff: every question has a kind, a `file:line`, and 3–4 choices, and none states
   its own answer. Rewrite a question or choice that gives the answer away before you ask it.
3. Ask one question at a time, in a pop-up with its choices in shuffled order when the harness has a
   multiple-choice tool (Claude Code: `AskUserQuestion`), else as a numbered list. The owner
   picks a choice **and** gives a one-line why (a note on the pick, or typed after). A pick alone
   never passes. If the why is missing, ask for it before saying anything about the pick. Then
   grade the pick and the why together, against the diff and the spec:
   - **understood**: the right choice with a why that holds.
   - **partial** (right choice, why doesn't hold) or **missed** (wrong choice): explain the point
     in 2–4 lines with a `file:line` pointer, then ask a rephrased question on the same point in
     free text. Repeat until understood. A free-text follow-up is understood if it holds against
     the diff, partial if incomplete, missed if wrong.
4. Append one `## examiner · quiz · <done|changes-requested>` block per round to `log.md`:
   each question, the answer as given, and its grade. Answers are stored nowhere else.
5. When every question ends understood: set `state.quiz` to `passed`, fill
   `metrics.understanding`, add the questions without answers to `pr-body.md` under
   "Check your understanding", checkpoint-commit, and present the gate.

While `state.quiz` isn't `passed`, an `approve` (typed, button, or `/spec-approve`) gets the
reply "the Understand quiz comes first". It isn't recorded, and it doesn't count as gate rework.
On resume, re-ask the questions that have no understood grade in `log.md`. A change request at
the Deliver gate that changes the diff sets `state.quiz` back to `pending`: the quiz runs again
on the new diff before the gate is shown again. A campaign runs one quiz per Deliver gate
([campaign.md](campaign.md)); on a pass, set `quiz` and copy `metrics.understanding` into every member's `state.json`.

## Gate presentation

Every gate message has the same shape so it's quick to scan:

```
⛔ <Gate> gate: <slug>
Summary: <2–4 lines>
Decide: <what exactly the user is approving>
Artifacts: specs/<slug>/<files>
Reply "approve", or say what to change.
```

**Ask with buttons when the harness can.** If it has a multiple-choice question tool (Claude
Code: `AskUserQuestion`), print the gate message without the last line, then ask with it:
"Approve" first, then "Request changes", plus one option per open choice in the spec (for
example a design alternative). Any typed answer still counts. Without such a tool, end with
the `Reply` line.

Deliver gate also lists, before `Artifacts:`, a `Changes:` line with the diff stat outside the
spec folder (`git diff --stat <base>...HEAD -- . ':!specs'`), so the work itself comes first,
and **every outward action verbatim**: branch to push, PR title, ticket comment text, and
status transition.
