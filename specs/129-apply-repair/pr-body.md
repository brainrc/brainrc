Add `apply --repair`: relink the links a moved checkout left broken

Part of epic #109 (E4), 5 of 6, stacked on #<PR_128>. Retarget to `main` before merging. Closes #129.

## Why
After you moved the checkout, every link brainrc made pointed at the old path. `apply` reported each one as a `CONFLICT` (142 on a full install) and linked nothing, and `doctor` told you to `rm` them one by one. A package upgrade to a new Python broke links the same way.

## What changed
- `apply --repair` relinks every broken link that points at the same item's old location (`skills/<name>`, `agents/<name>.md`, ...), and every link into a source root `apply` recorded in `$BRAINRC_HOME/harnesses.json`. Each shows as `REPAIR`.
- Links into the old location whose item is gone are pruned. Old locations come from the manifest and from the broken links themselves, so installs from before the manifest repair too.
- A broken link to anything else, or a working link to your own copy, stays a `CONFLICT`.
- `status --repair` shows the plan and writes nothing, and `--repair` works with `--only`.
- Without `--repair`, `status` and `apply` say how many of their conflicts it would fix. `doctor`'s fix for such a link is now `apply --repair`, not `rm`.
- docs/troubleshooting.md and docs/install.md use it.

## Acceptance criteria
- [x] AC1: move the checkout, `apply --repair`, and everything is in sync. Verified by `RepairTest`.
- [x] AC2: same-item broken links and links into recorded roots are relinked. Verified by `RepairTest`.
- [x] AC3: links to items that are gone are pruned, with or without a manifest. Verified by `RepairTest`.
- [x] AC4: other links stay conflicts. Verified by `RepairTest`.
- [x] AC5: `status --repair` writes nothing; `--only` works. Verified by `RepairTest`.
- [x] AC6: the hint and `doctor`'s fix. Verified by `RepairTest` and `DoctorTest`.

## How to verify
```
python3 -m unittest tests.test_repair
python3 -m unittest discover -s tests
```
Or by hand: `apply`, `mv` the checkout, then `python3 scripts/brainrc.py status --repair` and `apply --repair` from the new path.

## Decisions made without you
- Gates auto-approved (`--oneshot`): Spec, Plan, Deliver. See `specs/129-apply-repair/log.md`.
- "Same item" means the link's target ends with the same kind dir and name, and only a broken link qualifies. A link that still works is never taken unless it points into a root `apply` recorded.
- Repair stays opt-in: a plain `apply` still never replaces a link it doesn't recognise.

## Follow-ups
- None.

Spec: `specs/129-apply-repair/spec.md` · Plan: `specs/129-apply-repair/plan.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
