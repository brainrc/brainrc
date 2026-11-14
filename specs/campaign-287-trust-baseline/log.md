# Campaign gh:287 · trust baseline (E28)

## 2026-11-14T05:30:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:287 --shape ordered --dry-run`

- Prerequisite: E27 (#280) is on `main`: #281 to #286 are closed, and #346 and #351 are merged.
- Members: #288, #289, #290, #291. All open, none assigned, none skipped.
- Shape: `ordered` (given; the epic body says ordered). Dependency source: `none`: no links
  between the children, so the order is the epic's sub-issue order.
- Order: 1 #288 pin git packs to a commit · 2 #289 permission diff in `status` · 3 #290 pin MCP
  tool definitions · 4 #291 `brainrc audit`.
- Delivery: `sequential` (the epic body). Child N branches from child N-1; child 1 from `main`.
- No cycle, no link outside the epic. No playbook or parameter table (ordered shape).
- Main case: Gatework, the default git pack. Tests stay offline, with local bare repos as remotes.

## engine · Campaign gate · approved
The coordinator's brief (passing on the maintainer's ask to run E28 as a Gatework campaign) says to
dry-run, then build the children in order as draft PRs. Recorded as approved on that basis;
per-child Spec and Plan gates are logged here rather than stopped on. Merging stays with the
maintainer.

Delivery note: `sequential` opens only child 1's PR and waits for each merge. The brief asks for
every child's draft PR up, so each PR opens as a draft against `main` (never on another PR's
branch); PR N carries N-1's commits until N-1 merges. Merge them in order, merging `main` into the
next branch first (Retarget rule).

## engine · gh:288 · Spec and Plan (logged under the Campaign gate)
- Spec: the lock already records each git pack's commit (E27). Pin it: `apply`, `status` and
  `install` hold a git pack at the lock's commit while the config names the same `git` and `ref`;
  a fresh clone fetches the commit, not the ref, and a clone at another commit is put back.
  Editing `git` or `ref` is an intended move and unpins. `brainrc update [<pack>...]` moves the
  pin: refetch at the ref (50 commits deep), print `MOVED` with the commits between the pins and
  the installed files added, removed or changed (from the lock's hashes), then apply and relock.
  No lock spec change: `commit` was already required for git packs.
- Plan: `packs.py` (`pinned`, `to_fetch`, `fetch_pack(commit=, depth=)`, `commits_between`),
  `update.py` (new), `cli.py` and `project.py` pass the pins; tests in `tests/test_pins.py` and the
  two moved-tag tests in `tests/test_lock.py`.

## engine · gh:288 · verified
Draft PR #352 (base `main`). `validate` and the full suite passed before the push.

## engine · gh:289 · Spec and Plan (logged under the Campaign gate)
- Spec: record per pack, in the lock, `permissions` = `hooks` (fragment hook commands), `mcp`
  (servers), `tools` (agent `tools`, skill `allowed-tools`, other fragment keys) and `domains`
  (MCP URL hosts, `domain:` grants), only what the scope installs. `status` prints added and
  removed entries; `apply`/`update`/`install` ask before any added entry unless `--yes`, and
  refuse without a terminal. Decisions: a machine's first lock is the baseline (listed, not
  asked); a pre-permissions lock entry is the baseline only while the pack's files are unchanged;
  `install --frozen` never asks; no environment variable skips the question.
- Plan: `brainrc/permissions.py` (new), lock writer arrays, schema `permissions`, `cli.py` and
  `project.py` call the diff before writing, `check.py` compares records; tests in
  `tests/test_permissions.py`, fixtures in `tests/fixtures/lockfile/`.
