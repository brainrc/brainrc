# Spec: apply --repair for a moved checkout

Ticket: gh:129 · Size: standard · Status: approved

## Problem
After the checkout moves, every link brainrc made points at the old path. `apply` reports each
as a `CONFLICT` (142 on a full install) and links nothing, and `doctor` tells the user to `rm`
them one by one. A package upgrade to a new Python leaves the same breakage.

## Goals
- One command that relinks every link that pointed at the same item's old location.
- Links into the old location whose item no longer exists are pruned.
- Nothing else changes: a broken link to something else stays a conflict.

## Non-goals
- Repairing without being asked: a plain `apply` still never replaces a link it doesn't recognise.
- Moving the settings home (`migrate` does that).

## Acceptance criteria
- **AC1**: Given an applied checkout that is then moved, when the user runs `apply --repair` from the new location, then every link points into the new location and `status` says everything is in sync, with `doctor` clean.
- **AC2**: Given a broken link whose target ends with the planned source's kind dir and name (`skills/<name>`), or a link into a source root the manifest recorded, then `--repair` relinks it and prints `REPAIR`.
- **AC3**: Given links into the old location whose item is gone, then `--repair` prunes them; this also works with no manifest (old roots inferred from the repaired links).
- **AC4**: A broken link to a different item, or a working link to the user's own copy, stays a `CONFLICT` with `--repair`.
- **AC5**: `status --repair` prints the same plan and writes nothing; `--repair` combines with `--only`.
- **AC6**: Without `--repair`, `apply`/`status` say how many conflicts it would repair, and `doctor`'s fix for such a broken link is `apply --repair`.

## Requirement changes
### Area: aicfg-apply
#### ADDED: Repair links after a move
`brainrc apply --repair` (and `status --repair`, which writes nothing) SHALL relink a link whose target is under a source root recorded in the manifest, or is missing and ends with the planned source's last two path parts, and SHALL prune links whose item is gone that point into a recorded root, or into a root inferred from a broken link that no longer exists and is not ~ or one of its ancestors; it SHALL ignore recorded roots that are ~, / or an ancestor of ~, and every other link it doesn't manage, the user's live links included, SHALL stay as it is. (AC1, AC2, AC3, AC4, AC5)
### Area: doctor
#### ADDED: Repair hint
`brainrc doctor` SHALL give `apply --repair` as the fix for a broken link that names the same item as the planned source, and `rm` plus `apply` for any other broken link. (AC6)

## Open questions
None. Defaults taken under `--oneshot`:
1. "Same item" means the last two path parts match (kind dir and name), and only for a broken link, so a working link of the user's is never taken.
2. A link into a root the manifest recorded counts even when its target still exists, since apply made it.
