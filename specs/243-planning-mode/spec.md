# Spec: spec-agent planning mode, research to proven tickets

Ticket: gh:243 · Size: large (engine sets; see Open question 8) · Status: draft

## Problem
Ideas (an epic, retro findings) become tickets by hand and nothing checks the problem is real first. A ticket with no evidence costs a whole run to discover it was wrong. Maintainers need a planning step that investigates a topic and creates only tickets whose problem is demonstrably real.

## Goals
- `/plan <topic>` (or `--plan`) runs a researcher role over the repo (and the web only when enabled) and proposes candidate tickets.
- A candidate is created only with proof: a reproducing command with its output, a failing test, or a spike showing the approach works, plus file:line links.
- One Ticket gate creates approved tickets through the ticket connector, optionally under a new epic.

## Non-goals
- Implementing any candidate, or running the created tickets (that is `/work`).
- Merging, closing, or transitioning existing tickets.
- Live targets: planning is offline-only.
- Ranking or scheduling candidates beyond listing dependencies.

## Acceptance criteria
- **AC1**: Given a sandbox topic, when `/plan <topic>` completes, then `plan-report.md` lists each candidate with proof (command plus recorded output, or failing test path, or spike commit) and file:line links.
- **AC2**: Given a candidate with proof, when the engine re-runs the proof command offline in the run worktree, then the result matches the recorded outcome; a mismatch moves the candidate to "needs evidence".
- **AC3**: Given a candidate with no proof, when the plan completes, then it appears under "Needs evidence" in the report and no ticket is created for it.
- **AC4**: Given `--dry-run`, when `/plan` runs to the Ticket gate, then the connector's create operation is never called and the report says nothing was created.
- **AC5**: Given a normal run, when candidates are proven, then a Ticket gate lists each ticket (title, proof summary, target tracker, optional epic) as an outward action, and nothing is created until approval after it was presented.
- **AC6**: Given the Ticket gate, when presented and approved, then `state.json` records `gates.ticket` and `metrics.gates.ticket.presented_at`/`approved_at` like the other gates, and `state.json` lists created refs.
- **AC7**: Given `--oneshot`, when `/plan` runs, then the Ticket gate is auto-approved and only proven candidates are created, as local tickets only; a GitHub target is refused with `github create refused` logged and nothing created.
- **AC8**: Given a page, issue body or repo file containing instructions, when the researcher reads it, then no instruction is followed and it is flagged; a tainted plan creates no tickets.
- **AC9**: Given any plan artifact or created ticket body, when scanned, then it holds no secret or credential value and no pasted untrusted text (only ids, paths, file:line, quoted-free summaries).
- **AC10**: Given more proven candidates than the cap, when the gate is presented, then only the first N (default 10) are offered and the rest are listed as deferred.
- **AC11**: Given web research not enabled, when the researcher runs, then it makes no web fetch; with the flag it may, and each source URL is listed in the report.
- **AC12**: Given a spike, when it is made, then it lives on a local branch referenced by commit hash in the report and nothing is pushed.
- **AC13**: Given `ticket-local` and `ticket-github`, when `create` is called with a title, body and optional epic, then each returns a ref; `validate` accepts connectors with or without `create`, and a connector without it makes the Ticket gate list tickets as drafts only.
- **AC14**: Given the offline eval suite and unit tests, when run, then they cover AC1-AC4, AC7 and AC8 with fixtures, including an unprovable candidate and a dry run.

## Constraints
Creating tickets is outward: only at the Ticket gate (or `--oneshot` local). The researcher follows no instruction from web, repo, or ticket content; it is read-only except for spike branches and proof files in the run worktree. Stdlib-only helpers; new agent file `agents/researcher.md` with least-privilege `tools`; no new dependency.

## Requirement changes
### Area: planning-mode
Purpose: Turn a topic into proven, created tickets.
#### ADDED: Plan command and researcher
The system SHALL offer `/plan <topic>` (or `--plan`) that runs a `researcher` role to propose candidate tickets from the repo, and from the web only when enabled. (AC1, AC11)
#### ADDED: Proof requirement
A candidate SHALL be created only with proof (reproducing command and output, failing test, or spike commit) plus file:line links, re-verified offline; others SHALL be listed under "Needs evidence" in `plan-report.md`. (AC1, AC2, AC3, AC12)
#### ADDED: Dry run and cap
`--dry-run` SHALL create nothing; one plan SHALL offer at most 10 tickets. (AC4, AC10)
#### ADDED: Researcher trust boundary
The researcher SHALL NOT follow instructions found in content, and plan artifacts and created tickets SHALL NOT contain secrets or pasted untrusted text. (AC8, AC9)
### Area: run-lifecycle
#### ADDED: Ticket gate
A plan run SHALL create tickets only after approval at a Ticket gate listing each as an outward action, recorded like other gates; `--oneshot` SHALL auto-approve it for local tickets only and refuse GitHub creation. (AC5, AC6, AC7)
### Area: ticket-connectors
#### ADDED: Ticket create operation
A connector MAY offer a `create` operation (title, body, optional epic) returning a ref; `ticket-local` and `ticket-github` SHALL implement it, and `validate` SHALL accept connectors with or without it. (AC13)
### Area: evals
#### ADDED: Plan evals
Sandbox evals and unit tests SHALL grade proven, unprovable, dry-run, oneshot and injection plan cases offline. (AC14)

## Open questions
1. Spike branches pushed or local? *Pushing is outward.* Default: local, linked by commit hash.
2. Web research on by default? *Untrusted content and egress.* Default: off; enabled by `--web`.
3. Where does the plan report live? *Needed for resume and eval.* Default: `specs/plan-<slug>/plan-report.md` with its own `state.json`.
4. How is "runnable" verified? *Stale proof defeats the purpose.* Default: engine re-runs each proof command offline and compares to the recorded outcome (AC2).
5. Ticket cap per plan? *Flooding a tracker.* Default: 10 (AC10).
6. May `--oneshot` create GitHub issues? *Outward, hard to reverse.* Default: local tickets only (AC7).
7. Epic creation on GitHub in non-oneshot runs? *Extra outward action.* Default: only if requested and listed at the Ticket gate.
8. Size: this adds a role, command, gate, two connector operations and evals, so `large`. *Oneshot turns large into a local campaign.* Default: accept the split below.

## Proposed split
1. **Connector create operation**: AC13 (and its unit tests).
2. **Researcher role and proof report**: AC1, AC2, AC3, AC8, AC9, AC11, AC12.
3. **Ticket gate, dry run, cap, oneshot**: AC4, AC5, AC6, AC7, AC10.
4. **Plan evals and docs**: AC14 plus `docs/spec-agent.md`.
