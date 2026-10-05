# spec-agent

Takes a work item (GitHub issue, local markdown ticket, or a sentence) to a reviewed pull
request: **spec → plan → implement → verify → document → deliver**, run by an orchestrator
skill with a team of small, reusable agents. You approve at three gates. Everything else runs
on its own.

```
/work gh:42
  intake ─► analyst ─► ⛔ SPEC ─► architect ─► ⛔ PLAN ─► implementer ×N ─► reviewers ─►
  verifier ─► doc-writer ─► ⛔ DELIVER ─► push · PR · ticket update ─► retro
```

## Commands

| Command | Does |
|---|---|
| `/work <gh:42 \| issue URL \| local:path.md \| free text> [--local]` | Start, or resume if a spec for it exists. `--local`: drafts only, never push/PR/comment |
| `/spec-status [ref]` | Stage, gates, tasks, blocker, next action |
| `/spec-approve [notes]` | Approve the pending gate |
| `/spec-resume [ref]` | Continue an interrupted run (any tool) |

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

| | Claude Code | OpenCode | Codex / Gemini / Cursor |
|---|---|---|---|
| Skills + commands | ✅ | ✅ | ✅ (Cursor: skills only) |
| Execution | subagents per role | fallback (agents not yet adapted) | fallback: role-switch in one session |
| Per-agent model tiers | ✅ | — | — |
| Enforced guard hooks | ✅ | rules only | rules only |

## Extending

- **Agent:** add `agents/<name>.md` (frontmatter `name`, `description`, `tools`, `model`; body
  Role / Reads / Writes / Must not / Done when / Handoff), then reference it in the engine.
- **Domain skill:** add `skills/<name>/SKILL.md` with Validate / Conventions / Review checklist /
  Never-without-approval, then add a row to the Domains table in `skills/spec-agent/SKILL.md`.
- **Ticket connector:** add `skills/ticket-<system>/SKILL.md` implementing `fetch`, `comment`,
  `transition`, `link_pr`. Existing ones: `ticket-local`, `ticket-github`, `ticket-jira`.

`python3 scripts/aicfg.py validate` checks that every agent, skill, and link referenced exists.

## Credits

Stage structure inspired by GitHub's [spec-kit](https://github.com/github/spec-kit); small
artifacts and change-focused specs by [OpenSpec](https://github.com/Fission-AI/OpenSpec).
