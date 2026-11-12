# spec-agent

Takes a work item (GitHub issue, local markdown ticket, or a sentence) to a reviewed pull
request: **spec → plan → implement → verify → document → deliver**, run by an orchestrator
skill with a team of small, reusable agents. You approve at three gates. Everything else runs
on its own.

spec-agent is the engine of Gatework, brainrc's default pack ([packs.md](packs.md#default-packs),
[brainrc/gatework](https://github.com/brainrc/gatework)):
the `brainrc-gatework` skill. Its old names (`spec-agent`, `/spec-status`, `ticket-github` and the
other unprefixed skills) are deprecated aliases until 0.8.0.

> **Best effort outside Claude Code.** The design assumes each role starts with a fresh context
> and that hooks enforce the guardrails. That is fully true only in Claude Code. OpenCode runs
> real subagents, but without per-role models, and its hooks block instead of asking. Codex,
> Antigravity CLI, and Cursor have no named subagents, so the engine
> [switches roles in one session](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/fallback.md): reviewers have
> seen the implementer's reasoning, and the guardrails are instructions, not hooks. The fallback
> limits what reviewers read, and for standard and large runs it recommends a fresh session for
> review ([below](#harness-support)).

```
/brainrc-work gh:42
  intake ─► analyst ─► ⛔ SPEC ─► architect ─► ⛔ PLAN ─► implementer ×N ─► reviewers ─►
  verifier ─► doc-writer ─► ⛔ DELIVER ─► push · PR · ticket update ─► retro ─► watch
```

**`watch`** (normal delivery, connector with `pr_status`) runs on `/brainrc-gatework-resume`, never in a
loop. It reads the PR's checks; a red check caused by this diff becomes a fix task `C<n>`, run
through the usual implement and review loop, then a **Push gate** (diff stat, commits, the
failing check) before anything is pushed. External failures are only noted. Unresolved review threads are handled once each: a small
ask becomes a fix task `R<n>`, a question gets a drafted reply, and a design-level ask stops for
you. Replies post only after the same Push gate, and after 3 review rounds the PR is handed back.
After merge, `watch` verifies the merge commit in a detached worktree and records `pass`, `regression`, or `unverified`; a PR closed unmerged ends as `abandoned`, and both show in the summary. Details: [post-deliver.md](post-deliver.md). In a sandbox copy with
no git remote, `SPEC_PR_STATUS_FIXTURE` names a `pr_status` fixture file read instead of the connector.

## Commands

| Command | Does |
|---|---|
| `/brainrc-work <gh:42 \| issue URL \| local:path.md \| free text> [--local] [--auto] [--oneshot]` | Start, or resume if a spec for it exists. `--local`: drafts only, never push/PR/comment. `--auto`: no gate stops, ends with a draft PR ([Auto mode](#auto-mode)). `--oneshot`: like `--auto`, safer defaults, ready PRs ([Oneshot mode](#oneshot-mode)) |
| `/brainrc-gatework-status [ref]` | Stage, gates, tasks, blocker, next action |
| `/brainrc-gatework-approve [notes]` | Approve the pending gate |
| `/brainrc-gatework-resume [ref]` | Continue an interrupted run (any tool) |

These are user-invoked skills (`skills/brainrc-work/` and so on), so every harness that reads skills
gets them. In the Claude Code plugin they're `/gatework:brainrc-work`; in Codex, call the skill by name.

## Auto mode

`/brainrc-work <ref> --auto` (or `/brainrc-work --campaign <ref> --shape ordered --auto`) runs every stage without
stopping at the gates. It's for tickets you'd approve as written. Each gate is still written to
`log.md` as `auto-approved`, with its timestamps. Open questions take the analyst's stated default.
The run ends with a **draft** PR (a campaign: stacked draft PRs) whose body lists the gates and every
"Decision made without you". Review happens there.

Only the flag turns this on. No reply wording does, and a resumed run is gated again unless you pass
`--auto` again. These still stop the run, push nothing, and open no PR:
- any guardrails stop condition (retries, scope breach, spec gap, secrets)
- size `large` (the spec with its proposed split is written first)
- any plan Callout: a new dependency, an API or contract change, a migration, IAM/RBAC, prod config, or a destructive change
- a CRITICAL or HIGH security finding
- instructions in the ticket or other untrusted content
- a live target

Ticket comments stay drafts. Auto mode never merges, changes a PR's base, closes an issue, or
passes the `watch` Push gate, and `--local` still means nothing is pushed. Sandbox tickets
011–018 and eval cases `sandbox-008`–`015` grade it ([evals.md](evals.md)).

## Oneshot mode

`--oneshot` behaves as `--auto` with these differences, for tickets you want delivered without
babysitting:
- A `large` ticket splits into a local ordered campaign (no tracker tickets) run as `--oneshot`,
  delivered stacked.
- Plan callouts take the safer default (no new dependency; contract unchanged, or additive if the
  criteria need it; no migration or data change; destructive steps skipped; IAM/RBAC and prod config
  unchanged) and are listed under "Decisions made without you". If no default meets the acceptance
  criteria, the run blocks.
- A live target is refused and the run continues offline.
- PRs open ready, never merged. A tainted stop (CRITICAL/HIGH security finding, an instruction in
  untrusted content, a secret) pushes nothing and opens no PR, as `--auto` does. A benign stop
  (retry budget, scope breach, spec gap, no safe default) opens a draft PR titled
  `[blocked] <ticket ref>: <fixed phrase>` with a `## Blocked` section that names kinds and
  locations only. Any other stop counts as tainted. A blocked campaign child pauses the later children.
- `--oneshot` with `--auto` is `--oneshot`; `--local` still pushes nothing.

## Planning mode

`/brainrc-plan <topic>` turns a topic into proven tickets. A `brainrc-researcher` role reads the repo (the web
only with `--web`) and proposes candidates, each with proof: a read-only command and its
output, a failing test, or a local spike commit, plus `file:line` links. The engine re-runs each
command proof through `proof_guard.py`, a narrow read-only allowlist with no shell, network, or
secret files. Unproven candidates are listed under "Needs evidence" and never created. Content
the researcher reads is never obeyed; a plan that flags any instruction creates nothing.

The plan ends at a Ticket gate listing each ticket (at most 10) as an outward action; nothing is
created before you approve it. `--dry-run` creates nothing. `--oneshot` creates proven local
tickets only and refuses GitHub. State lives in `specs/plan-<slug>/`. Details:
[planning.md](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/planning.md).

## Design principles

1. **Files are the handoff.** Agents share no memory; each reads named artifacts in
   `specs/<slug>/` and returns a short handoff block. Any session, in any tool, can resume from
   `state.json`.
2. **Evidence over claims.** Tasks are done when commands prove it (tests, validators, plan
   summaries), not when an agent says so.
3. **Ceremony scales with risk.** Size (trivial → large) decides stages, gates, and whether
   subagents are worth spawning. Infra, IAM, migrations, and prod paths have a higher floor.
4. **Outward actions are gated twice**: by the Deliver gate in the workflow, and by
   harness hooks (Claude Code) that prompt on push, PR, cluster, cloud, and state mutations.
5. **Cheap by default.** Domain knowledge loads only for the stacks touched, command output stays
   in files, routine roles use cheaper models. See [efficiency.md](efficiency.md).

## Campaigns

`/brainrc-work --campaign <epic | query | refs> [--shape playbook|ordered]` runs many related tickets.
Two shapes, detected from the template check plus the children's depends-on links (`--shape` overrides):

- **playbook**: near-identical tickets. One shared playbook, approved at one Campaign gate, then
  batches with one Deliver gate per batch.
- **ordered**: different or dependent children, built in dependency order. Dependencies come from
  the connector (`api`, then `body`, then `frontmatter`; else epic order). Each child gets its own
  Spec and Plan gates. One Deliver gate covers all children and picks the delivery: `sequential`
  (only the first PR opens; resuming with `/brainrc-work --campaign` or `/brainrc-gatework-resume` opens the next after
  its predecessor merges) or `stacked` (all PRs open at once, each based on the previous child's
  branch). Either way a child PR merges only with base `main`: on resume after its predecessor
  merges, `main` is merged into its branch and a stacked PR is retargeted to `main`.

To express dependencies, use GitHub issue dependencies or a `Depends on #N` line in the child's
body. For local tickets, use `depends_on: [local:...]` in the child's frontmatter, and list the
children in the epic's `children:` (their order is the epic order).

Details: [campaign.md](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/campaign.md).

## Living specs

Each run's `specs/<slug>/` describes one change; `specs/living/<area>.md` describes how the
system behaves now, one file per capability area (`cli`, `export`). The analyst reads the areas
a ticket touches and writes the spec's `## Requirement changes`: ADDED, MODIFIED, and REMOVED
requirements against them, or `None.` In the document stage the engine applies that delta with
Gatework's `skills/brainrc-gatework/scripts/living_specs.py apply`, so the Deliver gate's diff shows the
behavior change next to the code. The script checks every block first (a MODIFIED or REMOVED
target must exist, an ADDED one must not) and writes nothing if any fails. Each requirement names
the run that last changed it. Formats: `templates/spec.md` and `templates/living.md`. Projects
that already have runs start with no living specs; the first run that touches an area creates it.

## Active run pointer

For tools outside the run's repo (a pack repo, a workspace root), spec-agent writes the active
run's absolute path to `$BRAINRC_HOME/active-run` (default `~/.config/brainrc/active-run`) at
intake, on resume, and at every checkpoint commit. The file is one line. It is not cleared when
a run finishes, and the last write wins across sessions. A tool reads it through
Gatework's `skills/brainrc-gatework/scripts/active_run.py read`, or falls back to the newest run in `<cwd>/specs/`
and every branch worktree's `specs/` when the file is absent or names a missing directory (detached task and verify worktrees are skipped). The contract is in [state.md](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/state.md#active-run-pointer).

## Run worktrees

Each run works in its own git worktree at `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`,
outside the repo and not under `$TMPDIR`. Your checkout is never touched, so you can keep
working in it. A run refuses to start or resume when your checkout is on the run's branch; switch away
first. The path is `state.worktree`, and `/brainrc-gatework-status` lists it for every run. `/brainrc-gatework-resume`
continues there and recreates a missing worktree from `state.branch`; if the branch is gone it
stops and says so.

Remove a worktree by hand with `git worktree remove <path>`. Cleanup on merge is planned
(#256). If your harness sandbox denies writes outside the repo, allow the directory (Claude Code:
`--add-dir <repo parent>/.brainrc-worktrees`).

## Roles (`agents/`)

| Agent | Model | Job |
|---|---|---|
| brainrc-analyst | sonnet | ticket → testable spec |
| brainrc-architect | opus | spec → approach + scope-fenced tasks |
| brainrc-implementer | sonnet | one task, test-first, in scope |
| brainrc-test-writer | sonnet | failing tests only (security logic, contracts) |
| brainrc-code-reviewer | sonnet | correctness + spec compliance |
| brainrc-security-reviewer | sonnet | exploitable issues |
| brainrc-infra-reviewer | sonnet | blast radius, destroy/replace, state, rollout |
| brainrc-verifier | haiku | criteria → evidence |
| brainrc-researcher | sonnet | topic → proven candidate tickets (`/brainrc-plan`) |
| brainrc-doc-writer | haiku | docs, PR body, ticket comment |

## Domain skills (`skills/`)

Loaded only when the work touches their files: `brainrc-go-service`, `brainrc-terraform` (incl. Terragrunt,
Atlantis, Spacelift), `brainrc-aws`, `brainrc-kubernetes` (Helm, Kustomize), `brainrc-gitops` (Argo CD, Flux),
`brainrc-ci-pipelines` (GitHub Actions), `brainrc-containers`, `brainrc-db-migrations`, `brainrc-observability`, `brainrc-scripting`
(Python, Bash). Each holds offline validation commands, conventions, a review checklist,
and what never to run without approval.

## Environments

Default is offline: validators, renderers, unit tests, local containers and databases. At
intake, you can allow specific targets for **read-only** evidence (a Terraform root to plan,
a kube context to diff, an AWS profile to read). Deploying (apply, sync, migrate on shared DBs)
is never part of a run. It happens after merge, by you, Atlantis/Spacelift, or GitOps.

## Harness support

| | Claude Code | OpenCode | Codex / Antigravity / Cursor |
|---|---|---|---|
| Skills + commands | ✅ | ✅ | ✅ (Cursor: skills only) |
| Execution | subagents per role | subagents per role (rendered agents) | fallback: role-switch in one session |
| Per-agent model tiers | ✅ | — | — |
| Enforced guard hooks | ✅ | ✅ plugin (deny only) | rules only (Cursor: shell and reads, deny only) |
| Independent reviewers | ✅ fresh context | ✅ fresh context | ⚠️ same session; reviewers read only spec, diff, and their role's inputs |
| Status | supported, E2E-tested | supported | best effort |

In fallback mode, the reviewer and verifier roles read only `spec.md`, the diff (`git diff
<base>...HEAD`), and the inputs their role file names. They never read `log.md` or the
implementer's handoffs, and the verifier re-runs every command it cites,
so the reasoning that produced the change can't argue for it. That narrows what a reviewer
reads; it doesn't make the context fresh, because the session still contains the earlier roles.
For standard and large runs the engine stops before batched review and recommends
`/brainrc-gatework-resume` in a new session. That is the only way to get an independent review there.

## Extending

- **Agent:** add `agents/<name>.md` (frontmatter `name`, `description`, `tools`, `model`; body
  Role / Reads / Writes / Must not / Done when / Handoff), then reference it in the engine.
- **Domain skill:** add `skills/<name>/SKILL.md` with Validate / Conventions / Review checklist /
  Never-without-approval, then add a row to the Domains table in `skills/brainrc-gatework/SKILL.md`. These live in
  [brainrc/gatework](https://github.com/brainrc/gatework); a private one goes in your own pack.
- **Ticket connector:** add `skills/ticket-<system>/SKILL.md` implementing `fetch`, `comment`,
  `transition`, `link_pr` per the
  [connector contract](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/connectors.md). `validate` checks the
  headings. Existing ones: `brainrc-ticket-local`, `brainrc-ticket-github`, `brainrc-ticket-jira`.
  Optional: `pr_status` (read-only; without it `watch` skips).

`python3 scripts/brainrc.py validate` checks that every agent, skill, and link referenced exists.

## Credits

Stage structure inspired by GitHub's [spec-kit](https://github.com/github/spec-kit); small
artifacts, change-focused specs, and living specs updated by ADDED/MODIFIED/REMOVED deltas by
[OpenSpec](https://github.com/Fission-AI/OpenSpec).
