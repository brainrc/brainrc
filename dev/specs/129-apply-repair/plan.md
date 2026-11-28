# Plan: apply --repair for a moved checkout

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** additive: `--repair` on `status` and `apply`; new link state `repair`.
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** with `--repair`, broken links that name the same item are replaced, and links into old roots are pruned.

## Approach
`Link.state` takes an optional list of old roots; with it, a link into one of them, or a broken
link whose target ends with the source's last two parts (`moved_item`), is `repair`. `_sync`
gathers the old roots for `--repair`: the manifest's (#126) not in use now, plus each root a
repaired link's target implies (`old_root`: the target minus the source's path in its root).
`plan()` takes those as extra roots for its stale check, so links into them whose item is gone are
pruned. `repair` is applied like `update`. Without `--repair`, conflicts that would repair are
counted in a hint, and `doctor` suggests `apply --repair` for them.

## Files
| File | Change |
|---|---|
| `brainrc/plan.py` | modify: `repair` state, `moved_item`, `old_root`, `plan(old_roots=)` |
| `brainrc/cli.py` | modify: `--repair` flag, old roots, hint |
| `brainrc/doctor.py` | modify: fix text for a moved link |
| `docs/troubleshooting.md`, `docs/install.md` | modify: use `--repair` |
| `tests/test_repair.py` | new |
| `tests/test_brainrc.py` | modify: doctor's fix for a moved link |
| `changelog.d/129-apply-repair.md` | new |

## Risks
- A broken link of the user's that happens to end in `skills/<same name>` is replaced. It was already broken, so nothing that worked is lost.

## Test strategy
Fake HOME, apply, move the checkout directory, then `status`, `apply --repair`, `status`, `doctor`. Variants: a renamed item, no manifest, `--only`, user links that must stay.

## Tasks
- [x] **T1** [agent: engine] repair state, old roots, flag, doctor hint, tests and docs
  - files: see Files
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6
