# Campaign gh:280 · project manifest and lockfile (E27)

## 2026-11-13T06:01:36Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:280 --shape ordered --dry-run`

- Members: #281, #282, #283, #284, #285, #286. All open, none assigned, none skipped.
- Shape: `ordered` (given; the epic body says ordered). Dependency source: `none`: no links
  between the children, so the order is the epic's sub-issue order.
- Order: 1 #281 spec and schemas · 2 #282 project scope · 3 #283 lock with commit and SHA-256
  per file · 4 #284 `install --frozen` · 5 #285 `check` · 6 #286 standards-first output.
- Delivery: `stacked` (the epic body). Child N branches from child N-1; child 1 from `main`.
- No cycle, no link outside the epic. No playbook or parameter table (ordered shape).
- Main case: default git packs (Gatework). A user-scope install with only Gatework must be
  fully locked.

## engine · Campaign gate · approved
The coordinator's brief for this run (passing on the maintainer's yes to building E27) says to
dry-run, then build the children in order as stacked draft PRs. Recorded as approved on that
basis; per-child Spec and Plan gates are logged here rather than stopped on, and delivery is
draft PRs only. Merging and retargeting stay with the maintainer.

## engine · Delivered · 2026-11-13
All six children built in order and opened as stacked draft PRs: #346 (#281, base `main`),
#347 (#282), #348 (#283), #349 (#284), #350 (#285), #351 (#286), each on the one before.
`validate` and the full test suite passed before each push. The epic's acceptance tests are
`test_two_machines_*` and `test_apply_on_two_fresh_machines_is_byte_identical` in
`tests/test_frozen.py`, and `test_a_moved_tag_*` there and in `tests/test_check.py`.
