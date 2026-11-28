# Spec: Refetch a git pack when its ref or URL changes

Ticket: gh:103 · Size: standard · Status: approved

## Problem
A pack named by `git` URL is fetched into `$AICFG_HOME/packs/<key>` only when that directory is
missing. A user who bumps `ref = "v1"` to `"v2"` (or moves the pack to a new URL) and runs
`apply` keeps the old checkout with no message, and `doctor` stays silent; only `aicfg update`
moves it. A git call that hangs (an unreachable host, a credential prompt) hangs `apply`.

## Goals
- `apply` fetches a git pack again whenever its configured `git` or `ref` differs from what was
  last fetched; `status` says it would.
- `doctor` reports a clone that doesn't match its config.
- No git call runs longer than 60 seconds.

## Non-goals
- Following a moving branch: with an unchanged `ref = "main"`, `apply` doesn't refetch to pick up
  new commits (`aicfg update` does, as today).
- Credential handling or prompts.

## Acceptance criteria
- **AC1**: Given a git pack fetched at `ref = "v1"`, when `ref` changes to `"v2"` and `apply`
  runs, then it prints the `FETCH` line, the clone is at v2, and v2's items are linked.
- **AC2**: Given the same change, when `status` runs, then it prints the `FETCH` line and the
  clone is unchanged.
- **AC3**: Given a git pack fetched from one URL, when `git` changes to another URL of the same
  pack and `apply` runs, then it fetches from the new URL.
- **AC4**: Given a clone whose fetched URL or ref differs from `packs.toml`, when `doctor` runs,
  then it reports a FAIL naming the fetched and the configured ref (or URL), with fix `apply`.
- **AC5**: Given an unchanged `git` and `ref`, when `apply` runs again, then it doesn't fetch
  (no `FETCH` line, no git call).
- **AC6**: Given a git call that runs past 60 seconds, then it is stopped and the command prints
  `ERROR git <cmd> timed out after 60s`, writes nothing, and exits 1.
- **AC7**: Given a clone fetched before this change (no record of what was fetched), when
  `status` runs, then it prints the `FETCH` line, and `apply` fetches once and records it.

## Constraints
- Stdlib only. The record lives with the clone under `$AICFG_HOME/packs/`, never in the user's repo.
- A clone with local changes is still never overwritten (existing error).

## Requirement changes

### Area: aicfg-config
#### ADDED: Git packs follow their config
`aicfg apply` SHALL fetch a git pack whenever its configured `git` URL or `ref` differs from the
one it last fetched (or none is recorded), `aicfg status` SHALL report that it would, and
`aicfg doctor` SHALL report the mismatch. (AC1, AC2, AC3, AC4, AC5, AC7)
#### ADDED: Git calls time out
aicfg SHALL stop any git call after 60 seconds and report it as an error. (AC6)

## Open questions
1. A clone from before this change has no record (AC7): fetch it once, or assume it matches and
   record the current config? *Fetching once needs the network on the first apply after
   upgrading; assuming could leave the exact bug this ticket fixes in place for anyone who
   already bumped `ref`.* Resolved at the Spec gate: fetch once.
