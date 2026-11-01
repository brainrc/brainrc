# Plan: Make the repo public

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none (gitleaks 8.24.3 is run once, from the release and checksum CI pins)
- **Public API / contract changes:** core's guard stops asking about `qm`/`pct`/`talosctl`; users who want those prompts enable `examples/pack-homelab`. Asked for by the ticket.
- **Migrations / data changes:** none
- **Security triggers touched:** guard hooks (security logic)
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Core `guard_outward.py` matches its `RULES` regexes against the raw command text, so a wrapped
`sh -c 'qm destroy 1'` is caught by the regex alone. The homelab pack's hook therefore needs only
those two rules plus the same PreToolUse output: a small stdlib script, no import from core
(a pack hook dir is a sibling of core's and may be a copy). The pack follows `examples/pack-acme`'s
layout, with `overrides/claude/hooks/` and a `settings.fragment.json` that uses `{{hooks_dir}}`.

The run records get `/home/user` replaced with `~`, and `state.md` says the engine writes
`worktree` that way, so new runs don't add home paths.

## Files
| File | Change |
|---|---|
| `overrides/claude/hooks/guard_outward.py` | modify: drop the qm/pct and talosctl rules and the docstring mention |
| `examples/pack-homelab/*` | new: pack.toml, README.md, hook, settings fragment |
| `tests/test_hooks.py` | modify: move the homelab cases to the pack hook; core no longer asks |
| `tests/test_brainrc.py` | modify: the homelab pack validates against the real VERSION |
| `docs/guardrails.md`, `docs/packs.md`, `examples/pack-acme/README.md` | modify: point to the homelab pack |
| `skills/spec-agent/references/state.md` | modify: `worktree` uses `~` |
| `specs/**` | modify: `/home/user` → `~` |
| `changelog.d/107-make-repo-public.md` | new |

## Risks
- The owner loses the homelab prompts until they enable the pack, mitigated by a follow-up line in the PR.

## Test strategy
Unit tests in `tests/test_hooks.py` (subprocess, like the harness) and `tests/test_brainrc.py`
(validate). AC5, AC7, AC8 by command evidence in `verify.md`.

## Tasks
- [ ] **T1** [agent: implementer] Move the homelab guards into `examples/pack-homelab`
  - files: `overrides/claude/hooks/guard_outward.py`, `examples/pack-homelab/pack.toml`, `examples/pack-homelab/README.md`, `examples/pack-homelab/overrides/claude/hooks/guard_homelab.py`, `examples/pack-homelab/overrides/claude/settings.fragment.json`, `tests/test_hooks.py`, `tests/test_brainrc.py`, `docs/guardrails.md`, `docs/packs.md`, `examples/pack-acme/README.md`, `changelog.d/107-make-repo-public.md`
  - criteria: AC1, AC2, AC3, AC4
  - review: each
- [ ] **T2** [agent: implementer] Remove home paths from run records; `worktree` uses `~`
  - files: `skills/spec-agent/references/state.md`, `specs/**`
  - criteria: AC5, AC6
