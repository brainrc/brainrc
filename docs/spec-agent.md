# spec-agent

Takes a work item (GitHub issue, local markdown ticket, or a sentence) to a reviewed pull
request: **spec → plan → implement → verify → document → deliver**, run by an orchestrator
skill with a team of small, reusable agents. You approve at three gates. Everything else runs
on its own.

> **Best effort outside Claude Code.** The design assumes each role starts with a fresh context
> and that hooks enforce the guardrails. That is fully true only in Claude Code. OpenCode runs
> real subagents, but without per-role models, and its hooks block instead of asking. Codex,
> Antigravity CLI, and Cursor have no named subagents, so the engine
> [switches roles in one session](../skills/spec-agent/references/fallback.md): reviewers have
> seen the implementer's reasoning, and the guardrails are instructions, not hooks. The fallback
> limits what reviewers read, and for standard and large runs it recommends a fresh session for
> review ([below](#harness-support)).

```
/work gh:42
  intake ─► analyst ─► ⛔ SPEC ─► architect ─► ⛔ PLAN ─► implementer ×N ─► reviewers ─►
  verifier ─► doc-writer ─► ⛔ DELIVER ─► push · PR · ticket update ─► retro ─► watch
```

**`watch`** (normal delivery, connector with `pr_status`) runs on `/spec-resume`, never in a
loop. It reads the PR's checks; a red check caused by this diff becomes a fix task `C<n>`, run
through the usual implement and review loop, then a **Push gate** (diff stat, commits, the
failing check) before anything is pushed. External failures are only noted. Review comments and
merge handling are not built yet. Details: [post-deliver.md](post-deliver.md). In a sandbox copy with
no git remote, `SPEC_PR_STATUS_FIXTURE` names a `pr_status` fixture file read instead of the connector.

## Commands

| Command | Does |
|---|---|
| `/work <gh:42 \| issue URL \| local:path.md \| free text> [--local]` | Start, or resume if a spec for it exists. `--local`: drafts only, never push/PR/comment |
| `/spec-status [ref]` | Stage, gates, tasks, blocker, next action |
| `/spec-approve [notes]` | Approve the pending gate |
| `/spec-resume [ref]` | Continue an interrupted run (any tool) |

These are user-invoked skills (`skills/work/` and so on), so every harness that reads skills
gets them. In the Claude Code plugin they're `/ai-config:work`; in Codex, call the skill by name.

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

`/work --campaign <epic | query | refs> [--shape playbook|ordered]` runs many related tickets.
Two shapes, detected from the template check plus the children's depends-on links (`--shape` overrides):

- **playbook**: near-identical tickets. One shared playbook, approved at one Campaign gate, then
  batches with one Deliver gate per batch.
- **ordered**: different or dependent children, built in dependency order. Dependencies come from
  the connector (`api`, then `body`, then `frontmatter`; else epic order). Each child gets its own
  Spec and Plan gates. One Deliver gate covers all children, then PRs open sequentially: only the
  first at once. Resuming (`/work --campaign` or `/spec-resume`) opens the next after its
  predecessor's PR is merged.

To express dependencies, use GitHub issue dependencies or a `Depends on #N` line in the child's
body. For local tickets, use `depends_on: [local:...]` in the child's frontmatter, and list the
children in the epic's `children:` (their order is the epic order).

Details: [campaign.md](../skills/spec-agent/references/campaign.md).

## Living specs

Each run's `specs/<slug>/` describes one change; `specs/living/<area>.md` describes how the
system behaves now, one file per capability area (`cli`, `export`). The analyst reads the areas
a ticket touches and writes the spec's `## Requirement changes`: ADDED, MODIFIED, and REMOVED
requirements against them, or `None.` In the document stage the engine applies that delta with
`skills/spec-agent/scripts/living_specs.py apply`, so the Deliver gate's diff shows the
behavior change next to the code. The script checks every block first (a MODIFIED or REMOVED
target must exist, an ADDED one must not) and writes nothing if any fails. Each requirement names
the run that last changed it. Formats: `templates/spec.md` and `templates/living.md`. Projects
that already have runs start with no living specs; the first run that touches an area creates it.

## Active run pointer

For tools outside the run's repo (a pack repo, a workspace root), spec-agent writes the active
run's absolute path to `$AICFG_HOME/active-run` (default `~/.config/ai-config/active-run`) at
intake, on resume, and at every checkpoint commit. The file is one line. It is not cleared when
a run finishes, and the last write wins across sessions. A tool reads it through
`skills/spec-agent/scripts/active_run.py read`, or falls back to `<cwd>/specs/` when the file
is absent. The contract is in [state.md](../skills/spec-agent/references/state.md#active-run-pointer).

## Roles (`agents/`)

| Agent | Model | Job |
|---|---|---|
| analyst | sonnet | ticket → testable spec |
| architect | opus | spec → approach + scope-fenced tasks |
| implementer | sonnet | one task, test-first, in scope |
| test-writer | sonnet | failing tests only (security logic, contracts) |
| code-reviewer | sonnet | correctness + spec compliance |
| security-reviewer | sonnet | exploitable issues |
| infra-reviewer | sonnet | blast radius, destroy/replace, state, rollout |
| verifier | haiku | criteria → evidence |
| doc-writer | haiku | docs, PR body, ticket comment |

## Domain skills (`skills/`)

Loaded only when the work touches their files: `go-service`, `terraform` (incl. Terragrunt,
Atlantis, Spacelift), `aws`, `kubernetes` (Helm, Kustomize), `gitops` (Argo CD, Flux),
`ci-pipelines` (GitHub Actions), `containers`, `db-migrations`, `observability`, `scripting`
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
`/spec-resume` in a new session. That is the only way to get an independent review there.

## Extending

- **Agent:** add `agents/<name>.md` (frontmatter `name`, `description`, `tools`, `model`; body
  Role / Reads / Writes / Must not / Done when / Handoff), then reference it in the engine.
- **Domain skill:** add `skills/<name>/SKILL.md` with Validate / Conventions / Review checklist /
  Never-without-approval, then add a row to the Domains table in `skills/spec-agent/SKILL.md`.
- **Ticket connector:** add `skills/ticket-<system>/SKILL.md` implementing `fetch`, `comment`,
  `transition`, `link_pr` per the
  [connector contract](../skills/spec-agent/references/connectors.md). `validate` checks the
  headings. Existing ones: `ticket-local`, `ticket-github`, `ticket-jira`.
  Optional: `pr_status` (read-only; without it `watch` skips).

`python3 scripts/aicfg.py validate` checks that every agent, skill, and link referenced exists.

## Credits

Stage structure inspired by GitHub's [spec-kit](https://github.com/github/spec-kit); small
artifacts, change-focused specs, and living specs updated by ADDED/MODIFIED/REMOVED deltas by
[OpenSpec](https://github.com/Fission-AI/OpenSpec).
