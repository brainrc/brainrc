# Gatework

Gatework takes a work item (a GitHub issue, a Jira key, a local markdown ticket, or a sentence) to
a reviewed pull request. Small agents write the spec, plan the work, implement it test-first,
review it, verify it against the spec and write the docs. You approve at three gates: the
**spec**, the **plan**, and **delivery** (the push, the PR and the ticket update). Everything in
between runs on its own, and every step leaves evidence in files.

It is brainrc's default pack, so `brainrc apply` installs it. It lives in its own repo,
[brainrc/gatework](https://github.com/brainrc/gatework). To leave it out, see
[packs](packs/use-a-pack.md#turn-the-default-pack-off-or-pin-it).

> **Best in Claude Code.** Each role gets a fresh context there, and the guard hooks are enforced.
> OpenCode also runs each role as its own subagent, but all on one model, and its hooks block
> instead of asking. Codex, Antigravity CLI and Cursor have no named subagents, so Gatework switches
> roles inside one session: the reviewers have seen the implementer's reasoning. Treat those three
> as best effort ([harness support](#harness-support)).

## Try it

```text
/brainrc-work gh:42
/brainrc-work local:tickets/7.md
/brainrc-work add a --dry-run flag to the sync command
```

```text
intake ─► analyst ─► ⛔ SPEC ─► architect ─► ⛔ PLAN ─► implementer ×N ─► reviewers ─►
verifier ─► doc-writer ─► ⛔ DELIVER ─► push · PR · ticket update ─► retro ─► watch
```

At each ⛔ gate the run stops and shows you what it wants approved. Answer with
`/brainrc-gatework-approve`, or ask for changes. To try it on a toy repo first, use the
[sandbox](../examples/sandbox/README.md).

## Commands

| Command | Does |
|---|---|
| `/brainrc-work <ref>` | start a run, or resume one if a spec for it already exists |
| `/brainrc-gatework-status [ref]` | show the stage, gates, tasks, any blocker and the next step |
| `/brainrc-gatework-approve [notes]` | approve the gate the run is waiting at |
| `/brainrc-gatework-resume [ref]` | continue an interrupted run, in any tool |
| `/brainrc-plan <topic>` | turn a topic into proven tickets ([planning](#planning)) |
| `/brainrc-review [focus]` | review uncommitted changes for bugs and security issues, outside a run |

`<ref>` is `gh:<number>`, a GitHub issue URL, `jira:<KEY-n>`, `local:<path>`, or free text.
These are skills, so every tool that reads skills gets them. In the Claude Code plugin they are
`/gatework:brainrc-work` and so on; in Codex, call the skill by name.

## How much it stops

| Flag | Gate stops | Ends with |
|---|---|---|
| none | spec, plan and delivery | a PR, after you approve the push |
| `--local` | spec, plan and delivery | drafts only: never pushes, opens a PR or comments |
| `--auto` | none | a **draft** PR |
| `--oneshot` | none, with safer defaults | a ready PR |

**`--auto`** is for tickets you'd approve as written. Each gate is still logged as
`auto-approved`, open questions take the analyst's stated default, and the PR body lists every
"Decision made without you". Only the flag turns it on; a resumed run is gated again unless you
pass `--auto` again. These still stop the run, push nothing and open no PR:

- a guardrails stop: too many retries, a change outside the plan's files, a gap in the spec, a
  secret;
- size `large` (the spec, with a proposed split, is written first);
- a plan callout: a new dependency, an API or contract change, a migration, IAM or RBAC, production
  config, or a destructive change;
- a CRITICAL or HIGH security finding;
- instructions found in the ticket or other untrusted content;
- a live target.

**`--oneshot`** works like `--auto`, but goes further on its own: a `large` ticket splits into a
local campaign, plan callouts take the safer default (no new dependency, no migration, contracts
unchanged), a live target is refused and the run continues offline, and PRs open ready. A stop for
a security finding, an injected instruction or a secret pushes nothing; any other stop opens a draft
PR titled `[blocked] ...` that says what blocked it.

Neither mode ever merges, changes a PR's base or closes an issue, and ticket comments stay drafts.

## Planning

`/brainrc-plan <topic>` turns a topic into tickets. A researcher role reads the repo (the web only
with `--web`) and proposes candidates, each with proof: a read-only command and its output, a
failing test, or a local spike commit. Gatework re-runs each proof, and lists unproven candidates
under "Needs evidence" without creating them. It stops at a Ticket gate (at most 10 tickets)
before creating anything. `--dry-run` creates nothing; `--oneshot` creates proven local tickets
only. Details: [planning.md](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/planning.md).

## Campaigns

`/brainrc-work --campaign <epic | query | refs>` runs many related tickets. It picks one of two
shapes from the tickets (`--shape` overrides):

- **playbook**, for near-identical tickets: one shared playbook approved once, then batches with
  one delivery gate each.
- **ordered**, for different or dependent tickets: each gets its own spec and plan gates, built in
  dependency order. One delivery gate picks `sequential` (one PR at a time, the next after its
  predecessor merges) or `stacked` (all PRs at once, each based on the previous branch).

Dependencies come from GitHub issue dependencies, a `Depends on #N` line, or, for local tickets,
`depends_on:` in the frontmatter. Details:
[campaign.md](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/campaign.md).

## After delivery

A run doesn't end at the PR. Each time you run `/brainrc-gatework-resume`, the `watch` stage reads
the PR:

- a red check this change caused becomes a fix task, reviewed like any other;
- a small review comment becomes a fix task, a question gets a drafted reply, and a design-level
  ask stops for you;
- a merged PR is verified again at the merge commit (`pass`, `regression` or `unverified`);
- a PR closed unmerged ends the run as `abandoned`.

Nothing is pushed or posted without your yes at a **Push gate**, and after three review rounds the
PR is handed back to you. It needs a ticket connector that can read PR status. Design and
details: [after delivery](post-deliver.md).

## Where a run keeps its state

- **`specs/<slug>/` in your repo**: the ticket, spec, plan, log, handoffs and `state.json`. Any
  session, in any tool, can resume from it.
- **Its own git worktree** at `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`, so your
  checkout is never touched. A run won't start while your checkout is on the run's branch. Remove
  a finished worktree with `git worktree remove <path>`. If your tool's sandbox blocks writes
  outside the repo, allow that folder (Claude Code: `--add-dir <repo parent>/.brainrc-worktrees`).
- **Living specs** in `specs/living/<area>.md` describe how the system behaves now. Each spec
  lists the requirements it adds, changes or removes, and the document stage applies them, so the
  delivery diff shows the behaviour change next to the code.
- **The active run** is recorded in `~/.config/brainrc/active-run`, for tools outside the repo
  ([contract](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/state.md#active-run-pointer)).

## Roles

| Agent | Model | Job |
|---|---|---|
| brainrc-analyst | sonnet | ticket → testable spec |
| brainrc-architect | opus | spec → approach and scope-fenced tasks |
| brainrc-implementer | sonnet | one task, test-first, in scope |
| brainrc-test-writer | sonnet | failing tests only (security logic, contracts) |
| brainrc-code-reviewer | sonnet | correctness and spec compliance |
| brainrc-security-reviewer | sonnet | exploitable issues |
| brainrc-infra-reviewer | sonnet | blast radius, destroy and replace, state, rollout |
| brainrc-verifier | haiku | acceptance criteria → evidence |
| brainrc-researcher | sonnet | topic → proven candidate tickets (`/brainrc-plan`) |
| brainrc-doc-writer | haiku | docs, PR body, ticket comment |

## Domain skills

Loaded only when the work touches their files, each with offline validation commands,
conventions, a review checklist and what never to run without approval. Gatework ships
`brainrc-ci-pipelines` (GitHub Actions), `brainrc-observability` and `brainrc-scripting` (Python,
Bash). Your own pack can add more ([your first pack](tutorial.md)).

Stack skills come from the official packs in [brainrc/packs](https://github.com/brainrc/packs),
which add them to the Domains table when enabled ([naming](packs.md#naming)):

| Pack | Domain skills |
|---|---|
| `brainrc/go` | `brainrc-go-service`, `brainrc-db-migrations` |
| `brainrc/terraform-aws` | `brainrc-terraform` (Terragrunt, Atlantis, Spacelift), `brainrc-aws` |
| `brainrc/kubernetes` | `brainrc-kubernetes` (Helm, Kustomize), `brainrc-gitops` (Argo CD, Flux), `brainrc-containers` |

Gatework shipped those seven skills itself up to 0.8. From 0.9, enable the packs for your stacks
to keep them ([upgrade](upgrade.md#gatework-09-stack-skills-moved-to-packs)). Python, Node and
TypeScript, and Rust have official packs there too.

## Environments

Runs are offline by default: validators, renderers, unit tests, local containers and databases.
At intake you can allow specific targets for **read-only** evidence, such as a Terraform root to
plan or a kube context to diff. Deploying is never part of a run; it happens after merge. Give
runs read-only credentials ([guardrails](guardrails.md#recommended-setup-for-runs-that-touch-infrastructure)).

## Harness support

| | Claude Code | OpenCode | Codex, Antigravity, Cursor |
|---|---|---|---|
| Skills and commands | ✅ | ✅ | ✅ |
| Execution | a subagent per role | a subagent per role | one session that switches roles |
| A model per role | ✅ | — | — |
| Guard hooks | ✅ | ✅ deny only | rules only (Cursor: shell commands and file reads, deny only) |
| Independent reviewers | ✅ fresh context | ✅ fresh context | ⚠️ same session |
| Status | supported, tested end to end | supported | best effort |

In the one-session fallback, reviewers and the verifier read only the spec, the diff and their
role's inputs, never the implementer's notes, and the verifier re-runs every command it cites.
That narrows what they read but doesn't give them a fresh context, so for standard and large runs
Gatework stops before review and suggests `/brainrc-gatework-resume` in a new session.

## Extend it

From your own pack, without touching Gatework, add `[extensions.gatework]` to `pack.toml`:
domain skills for your stacks, context skills to run at intake, a ticket connector for your
tracker, and checks for the delivery gate ([packs](packs.md#extensions)).

To change Gatework itself (a new role, a new connector), open a pull request on
[brainrc/gatework](https://github.com/brainrc/gatework). A domain skill for everyone goes in an
official pack in [brainrc/packs](https://github.com/brainrc/packs) instead. The
[connector contract](https://github.com/brainrc/gatework/blob/main/skills/brainrc-gatework/references/connectors.md)
says what a ticket connector must do.

## Design principles

1. **Files are the handoff.** Agents share no memory; each reads named files in `specs/<slug>/`
   and returns a short handoff.
2. **Evidence over claims.** A task is done when a command proves it, not when an agent says so.
3. **Ceremony scales with risk.** The ticket's size decides the stages and gates. Infrastructure,
   IAM, migrations and production paths start higher.
4. **Outward actions are gated twice**: by the delivery gate, and by the guard hooks.
5. **Cheap by default.** Domain skills load only for the stacks touched, command output stays in
   files, and routine roles use cheaper models ([efficiency](efficiency.md)).

Stage structure inspired by GitHub's [spec-kit](https://github.com/github/spec-kit); small
artifacts and living specs by [OpenSpec](https://github.com/Fission-AI/OpenSpec).

The name: Gatework's engine skill was called spec-agent before brainrc 0.7 ([old names](upgrade.md#from-spec-agent)).
