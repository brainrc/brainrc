# Campaign gh:121 · stack packs and official packs (E20)

## 2026-11-26T18:00:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:121 --shape ordered --dry-run`, worked by hand: the skill ships in
brainrc/gatework, which isn't installed in the build environment.

- Members: #121's own step (a pack from a folder of a git repo), #318 (domain skills out of core),
  #183 (python), #184 (node-ts), #185 (rust), #313 (starter), #314 (review), #315 (go), #316
  (terraform-aws), #317 (kubernetes), and #323 (security-baseline, from E11).
- Shape: `ordered`. Dependency source: `none`. The `subdir` key comes first: every pack lives in a
  folder of one repo, brainrc/packs. #318 comes next, because go, terraform-aws and kubernetes take
  over skills Gatework ships today.
- Delivery: core changes in one draft PR against `main`, one commit per child, since only one
  branch is pushable here. The packs are built as one folder each for brainrc/packs. That repo is
  empty, so its first commit goes straight to `main` and waits for the maintainer's yes.
- Starts from `main` at d1ffda5 (v0.8.31). Stays out of `brainrc/adapters/`; `brainrc/config.py` is
  also in E31's draft #389, so its two one-line edits sit away from #389's hunks (test-merged clean).

## engine · Campaign gate · approved
The coordinator's brief passes on the maintainer's go-ahead to build E20 as a campaign with draft
PRs and one brainrc/packs repo. Recorded as approved on that basis. Merging, tagging, the first push
to brainrc/packs and any Gatework change stay with the maintainer.

## engine · gh:121 · Spec and Plan
- A git pack may name `subdir`, the folder of the repo that is the pack: `[python] git = ".../packs.git"`,
  `ref = "v1.0.0"`, `subdir = "python"`. The clone stays whole at `packs/<key>/`; the pack root is
  the folder inside it. `subdir` must be a relative folder inside the repo (no `..`, no leading `/`
  or `-`), only goes with `git`, and a folder that is missing or links out of the clone fails the
  fetch with its name.
- The lock records `subdir` after `ref`; a lock with a `subdir` is version 3, one without stays 2,
  so older brainrc keeps reading locks that don't use it. `install --frozen` and `check` compare and
  honour it. Changing only the folder reuses the clone.
- Plan: `brainrc/sources.py` (`subdir`, `clone_root`, `in_clone`, `check_subdir`), `packs.py`,
  `lock.py`, `frozen.py`, `project.py`, `audit.py`, `config.py` (`subdir` is a layered key, dropped
  with the origin), both JSON Schemas and their fixtures, `docs/packs.md` (Packs from one repo),
  `docs/configuration.md`, `docs/project.md`, `docs/packs/use-a-pack.md`;
  `tests/test_pack_subdir.py` on local bare repos only.

## engine · gh:318 · Spec and Plan
- The domain skills ship in brainrc/gatework, not core, so core's part is to let a pack take one
  over: an item `exclude` leaves out is never installed, so it no longer collides. With
  `exclude = ["gatework:skills/brainrc-kubernetes"]`, the kubernetes pack and Gatework can be enabled
  together until Gatework drops its copy.
- The go, terraform-aws and kubernetes packs keep Gatework's skill names, so moving is a rename-free
  swap. Removing them from Gatework (and its Domains table) is a Gatework change and waits.
- Plan: `brainrc/sources.py` (`collisions` skips excluded items), `project.py`, `docs/packs.md`;
  tests in `tests/test_pack_subdir.py` (`TakeOverTest`).

## engine · gh:183, gh:184, gh:185 · Spec and Plan
- `brainrc/python`, `brainrc/node-ts` and `brainrc/rust` join `OFFICIAL_PACK_IDS` and the official
  table in `docs/packs.md`, which now links each pack's folder in brainrc/packs.
- Each pack: one `brainrc-<stack>` skill (Validate / Conventions / Review checklist / Never without
  approval), taken from the tool's own docs (Ruff, typescript-eslint, Clippy's CI page), eval cases
  in `evals/triggers.toml`, a permission manifest, its always-loaded token cost in its README.

## engine · gh:313, gh:314, gh:315, gh:316, gh:317, gh:323 · Spec and Plan
- starter: the smallest useful pack, for a setup with Gatework off. review: the review, PR
  description, commit message and unslop skills, for a setup with Gatework off. go, terraform-aws,
  kubernetes: Gatework 0.8's skills, grouped (go with db-migrations; terraform with aws; kubernetes
  with containers and gitops). security-baseline: guard denies for credential files, sandbox on.
- No trigger-eval harness runs yet (E30), so each pack ships its cases and says the delta is
  unmeasured.
