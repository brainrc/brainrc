# Campaign gh:112 · pack extension points (E10)

## 2026-11-20T07:15:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:112 --shape ordered --dry-run`, worked by hand: the skill ships in
brainrc/gatework, which isn't installed in the build environment.

- Members, in order: #140 (`[scope]`), #141 (declarative guard rules and the Claude evaluator),
  #142 (packs own settings keys), #143 (pack reviewers as roles), #144 (Gatework mode override),
  #145 (unavailable gates). All open, none skipped.
- Shape: `ordered` (given, and the epic body names it). Dependency source: `none`; the order is the
  epic's: scope first, since guard rules, deliver-check filtering and reviewers key on it.
- Delivery: the epic names `stacked`; the brief asks for one draft PR with one commit per child, as
  E7 and E8 ran, and only one branch is pushable here, so the children are commits on one branch.
- The epic's "start after #93 (E2)" is an ordering note; E2 is closed.
- Old issue bodies name `aicfg/`; the package is `brainrc/`. Extensions rendering and the Deliver
  gate now live in brainrc/gatework (its validator's `render_extensions`, its SKILL.md), which this
  campaign doesn't change: each child builds the core side, and the Gatework side is a follow-up there.

## engine · Campaign gate · approved
The coordinator's brief (passing on the maintainer's "Send E10 to coding") says to dry-run, then
build the children in order on one draft PR, review it, and stop before #143 while branch
`069-deliver-owner-quiz` is still live. Recorded as approved on that basis; per-child Spec and Plan
gates are logged here. Merging stays with the maintainer.

## engine · gh:140 · Spec and Plan (logged under the Campaign gate)
- Spec: `[scope]` in pack.toml with `remotes`, `paths`, `kube_contexts`, `aws_profiles` and
  `tickets`, each a list of globs; any match means the pack applies, none (or no table) means
  everywhere. Remotes match as written and as `host/owner/repo`; paths match the directory or an
  ancestor; tickets come from the branch name or `--ticket`. Read without running git or kubectl.
  `brainrc scope` says which packs apply where you are and why; `--extensions` renders
  extensions.md with only those packs, which is what a run should read. apply's extensions.md
  keeps every pack and ends with a Scope section.
- Done when "an acme pack's deliver checks don't show up in a personal-repo run": core's side is
  the filtered render; Gatework reading `brainrc scope --extensions` at intake is the follow-up.
- Plan: `brainrc/scope.py` (new), `brainrc/plugins.py`, `brainrc/validate.py`, `brainrc/cli.py`,
  the pack.toml schema, `examples/pack-acme`, docs/packs.md (Scope), docs/commands.md; tests in
  `tests/test_scope.py`.

## engine · gh:141 · Spec and Plan (logged under the Campaign gate)
- Spec: `[[guard.deny]]` and `[[guard.ask]]` with `reason` and one of `match` (a command: program,
  then words in order, each a glob) or `tool` (an MCP tool glob), and an optional `scope` in place
  of the pack's. apply renders them into `$BRAINRC_HOME/guard-rules.json` (pruned when none is
  left); `guard_outward.py` matches every unwrapped simple command and MCP tool against them under
  the scope of the payload's `cwd`. A pack deny wins over any ask. The hook carries a copy of the
  scope evaluator (it runs without brainrc installed); a parity test keeps the two in step.
- Only the Claude evaluator: the Cursor and OpenCode guards read the file in E11 (#116).
- Plan: `brainrc/guard.py` (new), `overrides/claude/hooks/guard_outward.py`, `brainrc/plan.py`,
  `brainrc/cli.py`, `brainrc/doctor.py`, `brainrc/validate.py`, `brainrc/uninstall.py` (purge list),
  the schema, the acme example, docs; tests in `tests/test_hooks.py` (risky and near-miss) and
  `tests/test_guard_rules.py`.

## engine · gh:142 · Spec and Plan (logged under the Campaign gate)
- Spec: a fragment's `permissions.allow`, `deny` and `ask` are unioned across enabled sources and
  merged after the user's entries; the ones brainrc added are recorded per settings file in
  `$BRAINRC_HOME/settings-owned.json`. A later apply removes owned entries no source lists any
  more; an entry the user had first is never owned. uninstall removes them. Other `permissions`
  keys keep set-when-missing.
- Plan: `brainrc/settings.py`, `brainrc/plan.py` (`SettingsMerge.wanted`), `brainrc/cli.py`,
  `brainrc/uninstall.py`, docs/packs.md (Permissions); tests in `tests/test_pack_settings_keys.py`.

## engine · before gh:143 · held
Branch `069-deliver-owner-quiz` is still on the remote (90c27b8, last commit 2026-11-10) with
commits `main` doesn't have; its PR #85 was closed unmerged on 2026-11-11 without a comment. The
brief says to stop here while it is live, so #143 to #145 wait for the maintainer to say whether
that branch landed elsewhere or was dropped. They also need changes in brainrc/gatework (its
SKILL.md, fallback roles, efficiency reference and Deliver gate).

## review · code-review (high) on PR #387, all 8 findings fixed in one commit
- gh:140: a misspelt `[scope]` key (`kube_context`) left a scope that applied everywhere; it is
  now a validate error naming the known key. A `URL =` line in `.git/config` was missed, and the
  hook's section regex differed from core's; both copies now agree, and the parity test checks it.
- gh:141: wrapper options that take a value (`sudo -u deploy`, `timeout 60`, `nice -n 5`,
  `env -C dir`, `env -S '...'`) hid the program from a deny rule; the hook now skips each
  wrapper's own options. A non-string `match` crashed `apply`, and a path or wrapper as its first
  word never matched; all three are validate errors.
- gh:142: a string where a permissions list belongs was split into characters; it is skipped. The
  minimal profile installs no settings fragment, so a pack's permissions don't land there; the
  Permissions section says so.
