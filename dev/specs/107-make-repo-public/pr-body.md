Move homelab guards to an example pack and drop home paths

Part of epic #95 (D1). Refs #107. It doesn't close #107: making the repo public and checking the install lines from a fresh VM are yours to do after merge.

## Why
The repo is about to go public. Core shipped guard rules that only fit the owner's homelab (Proxmox, Talos), run records committed under `specs/` held absolute home paths, and nobody had scanned the whole history for secrets.

## What changed
- Core's `guard_outward.py` no longer asks about `qm`/`pct` or `talosctl`. Host reboot and poweroff stay in core.
- New `examples/pack-homelab`: the first example pack with a guard hook (`guard_homelab.py`), with the same two rules, its settings fragment, and a README. The acme README and `docs/packs.md` link to it, and `docs/guardrails.md` points to it.
- The homelab test cases moved from core's guard tests to the pack hook, with new cases for wrappers, chaining, near-misses and bad payloads. A test checks that core stays silent on them.
- Run records under `specs/` write the home directory as `~`. `state.md` now says `worktree` is written that way, so new runs don't commit home paths.

## Acceptance criteria
- [x] AC1: core doesn't ask about the homelab commands and still asks about `sudo reboot`. Verified by `HomelabGuardTest.test_core_no_longer_asks` and `GuardOutwardTest`.
- [x] AC2: the pack hook asks about them (plain, `sh -c`, after `;`), passes read-only commands, and ignores bad payloads. Verified by `HomelabGuardTest`.
- [x] AC3: `validate --pack examples/pack-homelab` passes. Verified by `ExamplePackTest` and the fragment test.
- [x] AC4: `docs/guardrails.md` points to the pack.
- [x] AC5: no `(/Users/|/home/)<name>` paths in the tree, apart from the CI runner's `/home/runner`. Verified by `rg`.
- [x] AC6: `state.md` says `worktree` is written with `~`.
- [x] AC7: gitleaks 8.24.3 (CI's pinned release and checksum) scanned all 789 non-merge commits on every branch and found no leaks, both with the repo's `.gitleaksignore` and without it.
- [x] AC8: no `bxker` outside `CHANGELOG.md` and `specs/`.

## How to verify
```
python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
python3 scripts/brainrc.py validate --pack examples/pack-homelab
gitleaks git --redact --log-opts="--all" .
```

## Decisions made without you
- Gates auto-approved (`--oneshot`): Spec, Plan, Deliver. See `specs/107-make-repo-public/log.md`.
- `CHANGELOG.md` and old run records keep their `bxker/ai-config` links. They are released history, and GitHub redirects them.
- Host reboot and poweroff stay in core, since they are not homelab-specific.
- The pack hook copies the two regex rules and doesn't import core. A pack's hooks dir is a sibling of core's and may be a copy. Core's rules match raw text, so wrapped commands are still caught.
- Security trigger touched (guard hooks). Review findings are listed below.
- Ticket comment not posted: `specs/107-make-repo-public/ticket-comment.md`.

## Follow-ups
- **You:** enable `examples/pack-homelab` in your `packs.local.toml` to keep the Proxmox and Talos prompts.
- **You, a history question:** 58 early commits carry a personal author email rather than the GitHub noreply address. Removing it means rewriting history before going public. Gitleaks doesn't flag it.
- **You:** flip the repo to public, then check the install lines from a fresh VM (the rest of #107's "Done when").
- CI doesn't run the pre-commit no-home-paths check. A CI step would catch a home path in a committed run record.

Spec: `specs/107-make-repo-public/spec.md` · Plan: `specs/107-make-repo-public/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01Hn6pdU7RJ1sLQqc3fDP7Sa
