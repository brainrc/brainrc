# Spec: Make the repo public

Ticket: gh:107 · Size: standard · Status: approved

## Problem
The repo is about to become public. Core still ships guard rules that only fit the owner's
homelab (Proxmox `qm`/`pct`, `talosctl`), so every stranger who installs it gets them. Run records
committed under `specs/` hold absolute home paths (the run worktree path), which the repo rules
forbid, and every new run would add another. Nobody has scanned the whole history for secrets.

## Goals
- The homelab guards live in an example pack that anyone, the owner included, can enable.
- No absolute home path in the tracked tree, and new runs record the worktree with `~`.
- A clean gitleaks scan of every commit, with the evidence recorded.

## Non-goals
- Flipping the repo to public and the fresh-VM install check: owner actions after merge.
- Rewriting git history (author emails, old URLs in past commits).
- Editing `CHANGELOG.md` entries that name the old `bxker/ai-config` URL: released history.
- A CI step for the no-home-paths check.

## Acceptance criteria
- **AC1**: Given core's `guard_outward.py`, when the command is `qm destroy 105`, `pct stop 200`
  or `talosctl -n 10.0.0.2 upgrade --image x`, then it gives no decision; `sudo reboot` and
  `sudo halt` are still asked about.
- **AC2**: Given `examples/pack-homelab`, when its `guard_homelab.py` hook gets those three
  commands, plain or inside `sh -c '…'`, then it asks; for `qm list`, `pct list` and
  `talosctl -n 10.0.0.2 dashboard` it gives no decision; a malformed payload or a non-Bash tool
  gives no decision.
- **AC3**: Given `examples/pack-homelab`, when `brainrc validate --pack examples/pack-homelab`
  runs, then it passes, and the pack's `settings.fragment.json` runs the hook from `{{hooks_dir}}`.
- **AC4**: Given `docs/guardrails.md`, when read, then the core list no longer names Proxmox or
  Talos, and it points to the homelab example pack for them.
- **AC5**: Given the tracked tree, when searched for `(/Users/|/home/)<name>` outside
  `/home/runner` (the CI runner), then there are no matches.
- **AC6**: Given `skills/spec-agent/references/state.md`, when read, then it says `worktree` is
  written with the home directory as `~`.
- **AC7**: Given gitleaks 8.24.3 (CI's pinned version and checksum), when it scans every commit
  on every branch, then it finds no leaks, with the repo's `.gitleaksignore` and without it.
- **AC8**: Given docs other than `CHANGELOG.md` and `specs/`, when searched for `bxker`, then
  there are no matches.

## Constraints
Hooks stay stdlib-only. New guard patterns need a risky command and a safe near-miss test.
No new dependency: gitleaks is run once from the pinned release CI already uses.

## Requirement changes
### Area: guard-hooks
Purpose: What the core and example-pack guard hooks ask about before a command runs.
#### ADDED: Homelab guards in an example pack
Core's outward guard SHALL NOT ask about Proxmox `qm`/`pct` or `talosctl` commands. The
`examples/pack-homelab` hook SHALL ask about `qm`/`pct` destroy/stop/shutdown/reboot/reset/
rollback/migrate and `talosctl` apply-config/upgrade/upgrade-k8s/reset/reboot/shutdown/bootstrap,
and stay silent for read-only commands. (AC1, AC2, AC3)

### Area: run-lifecycle
#### ADDED: Worktree path without the home directory
`state.json` `worktree` SHALL be written with the home directory as `~`. (AC6)

## Open questions
None. Defaults taken under `--oneshot`:
1. Old URLs in `CHANGELOG.md` and run records stay: they are history, and GitHub redirects them.
2. Host reboot/poweroff stays in core: it is not homelab-specific.

## Proposed split
