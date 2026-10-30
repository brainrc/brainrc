# Changelog

The core version lives in [`VERSION`](VERSION). Packs pin it with `requires_core`
([docs/packs.md](docs/packs.md#compatibility)).

Entries tagged **[pack contract]** change what packs can rely on: `pack.toml` keys and
extensions, the rendered `extensions.md`, naming and layout rules. While the version is `0.x`,
a breaking pack-contract change bumps MINOR. After `1.0`, it bumps MAJOR. Everything else
(new skills, fixes, docs) bumps PATCH.

Every PR adds a fragment in [`changelog.d/`](changelog.d/README.md). On merge, the release
workflow folds the fragments in under the next version, bumps `VERSION`, and tags `vX.Y.Z`.
There is no Unreleased section: `main` is what users pull, so `VERSION` always describes it.

## 0.5.2 (2026-10-30)

- spec-agent runs now work in their own git worktree at `<repo parent>/.brainrc-worktrees/<repo-name>/<slug>`, so your checkout is never touched. A run refuses to start when your checkout is on the run's branch.
- `/spec-resume` and `/spec-status` locate runs through `state.worktree`; resume recreates a missing worktree from `state.branch`. With no usable active-run pointer, `active_run.py read` also scans every branch worktree.

## 0.5.1 (2026-10-30)

- Record the rename follow-ups (#236, #237, #239) as done, with their post-merge verifies.

## 0.5.0 (2026-10-29)

- **[pack contract]** 0.5.0 removes the old names that have warned since 0.4.0. Use `brainrc` for the `aicfg` command, `scripts/brainrc.py` for `scripts/aicfg.py`, and `python -m brainrc` / `import brainrc` for `python -m aicfg` / `import aicfg` (the `aicfg_home` alias is gone too). Use `BRAINRC_HOME` for `AICFG_HOME`. The legacy `~/.config/ai-config` and `AICFG_HOME` are no longer read: while either holds an unmigrated home, `status`, `apply` and `update` write nothing and exit 1 naming `brainrc migrate`, and `doctor` reports a FAIL. Run `brainrc migrate` to move it. Packs should allow `requires_core` `<0.6`.
- Record the brainrc rename campaign (#199) as done: #209's post-merge verify and retro, and the campaign log.

## 0.4.7 (2026-10-29)

- `apply` now writes brainrc names for the Codex MCP block markers, the OpenCode guard link (`brainrc-guard.js`) and the git pack fetch record (`.git/brainrc-fetched.json`). It still recognizes the old ai-config ones: it replaces an old Codex block in place, prunes the old guard link when it points at the managed guard, and reads then removes the old fetch record, so nothing is duplicated or re-fetched.

## 0.4.6 (2026-10-29)

- `validate` and `release` refuse changelog fragments whose bump would release the version that
  removes the deprecated `aicfg` names (`SHIM_REMOVED_IN`) while those names still exist.
- spec-agent: an auto Spec gate is never approved while `living_specs.py check` fails;
  dispatches quote spec and plan rules word for word; the analyst writes MODIFIED blocks as the
  requirement's full new text. Tests clear `XDG_CONFIG_HOME`, so they behave the same locally as
  on CI.

## 0.4.5 (2026-10-28)

- **[pack contract]** Everything now says brainrc. These old names keep working with a warning until 0.5.0 removes them: the `aicfg` command, `scripts/aicfg.py`, `python -m aicfg`, `import aicfg`, `AICFG_HOME` and the legacy `~/.config/ai-config` home. Run `brainrc migrate` to move the home.
- The next `apply` converges these silently: old `hooks/ai-config*` dirs and their settings entries, and `.bak-aicfg-*` backups.
- `brainrc doctor` flags the old `ai-config@ai-config` plugin until you uninstall it.
- Docs, README, AGENTS.md, CONTRIBUTING.md, skills, the example pack, messages and the pre-commit hook id now say brainrc.
- Some on-disk names are kept for compatibility and will change in a later follow-up: the Codex MCP block markers, the OpenCode `ai-config-guard.js` link and `.git/aicfg-fetched.json`.

## 0.4.4 (2026-10-28)

- **[pack contract]** The plugin and marketplace are now named `brainrc` (`brainrc@brainrc`) for
  Claude Code, Codex, Cursor and Antigravity; in Claude Code, skills and agents show as
  `brainrc:<name>` (`/brainrc:work`). Plugin users uninstall `ai-config@ai-config` and its
  marketplace, then install `brainrc@brainrc`
  ([moving from ai-config](docs/install.md#moving-from-ai-config)); `brainrc doctor` warns while
  the old plugin is still installed in Claude Code or Cursor. Packs whose plugin `dependencies`
  name `ai-config` must name `brainrc`.

## 0.4.3 (2026-10-28)

- **[pack contract]** Hook links are now `hooks/brainrc` and `hooks/brainrc-<pack>` (was `hooks/ai-config*`). The next apply replaces old-name settings and hooks.json entries, removes the old links, and honors MCP ownership records left in a former home. Backups are `.bak-brainrc-*`; old `.bak-aicfg-*` count toward the 5 kept. Packs using `{{hooks_dir}}` need no change; hard-coded `hooks/ai-config` paths do.

## 0.4.2 (2026-10-28)

- **[pack contract]** The settings home is now `~/.config/brainrc` (`$XDG_CONFIG_HOME/brainrc`
  when that is set), overridden by `BRAINRC_HOME`. Rendered `instructions.md` and
  `extensions.md`, git packs, `*.local.toml`, and `rules/*.local.md` live there. An existing
  `~/.config/ai-config`, or `AICFG_HOME`, keeps working until 0.5.0 with one warning per run.
  `brainrc migrate` (try `--dry-run` first) moves the old directory and re-runs `apply`.
  `brainrc doctor` reports an old home that hasn't been migrated, and spec-agent's run pointer
  follows the same lookup. Reading `XDG_CONFIG_HOME` closes #131.

## 0.4.1 (2026-10-28)

- The example pack accepts core 0.4 (`requires_core = ">=0.3, <0.5"`), and the pack examples in
  docs/tutorial.md and docs/packs.md pin `>=0.4, <0.5`. The 0.4.0 bump left them at `<0.4`, so
  `validate --pack examples/pack-acme` failed and a pack copied from the tutorial was rejected.

## 0.4.0 (2026-10-28)

- **[pack contract]** The tool is now `brainrc`: the PyPI distribution, the console script, the
  Python package (`import brainrc`, `python -m brainrc`), and the checkout entry
  `scripts/brainrc.py`. `brainrc --version` prints `brainrc <VERSION>`. The old names
  (`aicfg`, `scripts/aicfg.py`, `python -m aicfg`, `import aicfg`) keep working until 0.5.0,
  each printing one deprecation line on stderr; point packs' pre-commit hooks at
  `scripts/brainrc.py` before then. Installed users: run `uv tool uninstall ai-config` (or
  `pipx uninstall ai-config`) before installing `brainrc`, because both ship an `aicfg` command
  and removing the old one afterwards deletes the new shim. `AICFG_HOME` and
  `~/.config/ai-config` are unchanged for now.

## 0.3.50 (2026-10-28)

- Install commands and issue links in the docs point at `brainrc/brainrc` instead of going
  through the old repo's redirect, and `pyproject.toml` lists the repo and issue URLs.

## 0.3.49 (2026-10-27)

- CI: bump `actions/checkout` to v7.0.1 and `actions/setup-python` to v7.0.0 (full-SHA pins) in the validate and release workflows, moving them off the deprecated Node 20 runtime to Node 24. (gh:220)

## 0.3.48 (2026-10-27)

- `/work <ref> --auto` runs spec-agent without gate stops and ends with a draft PR. A campaign run with `--shape ordered --auto` ends with stacked draft PRs. Each gate is logged as `auto-approved`, and the PR body lists the "Decisions made without you". Only the flag turns it on. Hard stops still stop and push nothing: guardrails stop conditions, size `large`, any plan Callout, a CRITICAL/HIGH security finding, instructions in untrusted content, and live targets. Ticket comments stay drafts, and the Push gate is unchanged. Sandbox tickets 011–018 and eval cases `sandbox-008`–`015` grade it (gh:216).

## 0.3.47 (2026-10-27)

- `validate`, `status`, `apply`, and `doctor` refuse two enabled packs with the same `name`, naming both `packs.toml` keys, and a pack named `core`. Before, the two shared one hooks dir and `apply` never settled (gh:101).
- `apply` and `status` run the checks `validate --pack` runs on each enabled pack before linking anything. A pack skill without the pack's prefix, or any other pack error, is printed and nothing is written. Before, `apply` linked it and exited 0 (gh:102).
- `apply` fetches a git pack again when its `ref` or `git` URL changes, and `status` shows the `FETCH` line first. Before, a pack was fetched only when its clone was missing, so bumping `ref` did nothing. The fetched URL and ref are recorded in the clone's `.git/aicfg-fetched.json`, and clones from older versions are fetched once. `doctor` reports a clone that doesn't match its config. Git calls stop after 60 seconds instead of hanging `apply` (gh:103).
- `validate` accepts an agent `model` given as a full Claude model ID (`claude-sonnet-5-5`) and `Task` in `tools`. Other model and tool names still fail (gh:202).

## 0.3.46 (2026-10-27)

- Bad config in `harnesses.toml`, `packs.toml`, their `.local.toml` overrides, or a pack's `pack.toml` now prints `ERROR <file>:<line>: <what>` and exits 1 before anything is written. Before, a syntax error showed a traceback, `claude = false` raised `TypeError`, and `enabled = "false"` counted as enabled. Unknown keys and harness tables only the local file defines (`[cursr]`) print a `WARN` with file and line instead of being ignored (gh:100).
- `aicfg doctor | head` and other early-closed pipes exit quietly instead of printing a `BrokenPipeError` traceback.

## 0.3.45 (2026-10-27)

- An installed `aicfg` copies core's guard hooks to `$AICFG_HOME/hooks/core/` and links them from there, so they keep working when `uv tool upgrade` or `pipx upgrade` moves the tool to a new Python. `status` reports a copy that no longer matches the package, and the next `apply` refreshes it. Checkouts still link hooks live.

## 0.3.44 (2026-10-26)

- Guard hooks fail open when their script is missing, so a moved or deleted checkout (or a Python upgrade) no longer blocks every Claude Code tool call. Cursor's guard replies allow. Run `apply` to rewrite existing hook commands.
- `aicfg doctor` runs each ai-config hook with an empty payload and reports one that is missing, exits non-zero, times out, or has no `python3`.

## 0.3.43 (2026-10-26)

- `aicfg apply` takes a lock on `$AICFG_HOME/apply.lock`, so a second apply exits with a clear message instead of overwriting the first one's writes. Temp files carry the pid. A settings or MCP file that changes while apply runs (Claude Code rewriting `~/.claude.json`) is left alone with a `CHANGED` warning and exit 1, instead of losing that write.

## 0.3.42 (2026-10-26)

- `aicfg apply` keeps a settings or MCP file's permissions when it rewrites it, so a `0600` `~/.claude.json` no longer comes back world-readable, and writes through a symlinked file to its target instead of replacing the link. Backups keep the original's permissions and sit next to the target.

## 0.3.41 (2026-10-26)

- The release workflow creates a GitHub Release for each `vX.Y.Z` tag, with that version's `CHANGELOG.md` section as its notes. It skips a release that already exists. `python3 scripts/aicfg.py release --notes X.Y.Z` prints those notes.

## 0.3.40 (2026-10-26)

- CI runs the pinned gitleaks CLI (8.24.3, checksum-verified) instead of `gitleaks-action`, which fails without a paid license now that the repo is owned by an organization. It scans the same commit range with the same flags.

## 0.3.39 (2026-10-25)

- Ordered campaigns: the Deliver gate picks `sequential` or `stacked` delivery, and a retarget rule makes every child PR merge with base `main` (gh:77's stacked PRs merged into their stacked bases). Adds member status `verified`, a single home for `campaign.json`, and a `stacked` mode for the `campaign` eval check.
- spec-agent: `worktree_fence.py` checks a wave task's changed paths against its `files` and the main tree before landing, and status checks use `git -C <worktree>`. The architect puts a task that links to another task's new file in a later wave. `SKILL.md` says when the engine may edit an approved artifact itself.

## 0.3.38 (2026-10-25)

- spec-agent gains a `watch` stage after delivery: on `/spec-resume` it reads the PR's checks, records failures it can't attribute to the diff as `external`, and turns own failures into fix tasks `C<n>` that run through the normal review loop. Pushing a fix needs approval at a new Push gate. `SPEC_PR_STATUS_FIXTURE` lets offline evals supply `pr_status`. Review comments and post-merge verify remain planned.
- spec-agent `watch` now handles unresolved PR review threads: a small ask becomes a fix task `R<n>`, a question gets a drafted reply, and a design-level ask stops for the user. Replies post via `reply_thread` only after approval at the Push gate, thread text is treated as untrusted (embedded instructions are flagged), each thread is handled once via `watch.thread_log`, and the PR is handed back after 3 review rounds. Post-merge verify remains planned.
- spec-agent `watch` now handles a merged or closed PR: a merged one is verified at the merge commit in a detached worktree (`pass`, `regression`, or `unverified`, with a suggested follow-up on regression), a closed one ends as `abandoned`, and `retro.md` gains an `## After delivery` section. `retro_report.py` adds Outcome, Post-merge, Time to merge, Review rounds, and CI failures per run, plus average time to merge and merged, abandoned, and regression counts; `--json` is `schema_version` 2.

## 0.3.37 (2026-10-24)

- Connector contract gains an optional read-only `pr_status` operation (head checks, unresolved review threads, merge state; thread text fenced as untrusted). A connector without it makes `watch` skip. `ticket-github` implements it (read-only `gh` and GraphQL calls), and offline `pr_status` fixtures (red CI, review comment, merged) ship in `examples/sandbox/`.

## 0.3.36 (2026-10-21)

- Add the `ordered` campaign shape (children built and merged in dependency order), the `--shape` flag, and a `dependencies` connector op (ticket-github, ticket-local).
- Document campaign shapes in docs/spec-agent.md and the `campaign` eval check kind in docs/evals.md.
- Add a sandbox epic (`004-greeting-epic`) with out-of-order children to try the ordered shape.

## 0.3.35 (2026-10-21)

- Add `scripts/retro_report.py`: offline rollup of run metrics across `specs/*/state.json` (Markdown or `--json`), with optional period-total tokens and cost via `--ccusage`.
- Document the rollup, what each number means, and the JSON schema in `docs/efficiency.md`; roadmap item moved to Done.

## 0.3.34 (2026-10-21)

- spec-agent records the active run's path in `$AICFG_HOME/active-run` (new `active_run.py write|read`) at intake, resume, and every checkpoint, so external tools can find the current run.

## 0.3.33 (2026-10-19)

- spec-agent: `living_specs.py` ignores a note before the first `### Area:` under
  `## Requirement changes` (two sandbox runs wrote one, apply rejected it, and the engine edited
  `spec.md` after approval). The engine also runs `living_specs.py check` before presenting the
  Spec gate, so a malformed delta is fixed before it is approved.

## 0.3.32 (2026-10-18)

- spec-agent: dispatch puts the skills a role file names on a new `Role skills:` line with
  absolute paths (doc-writer: pr-description, doc-types, unslop, runbook; security-reviewer:
  security-checklist). Roles have no skill tool, so the doc-writer couldn't load them.
- spec-agent: `specs/<slug>/.runs/` ignores itself with its own `.gitignore` (`*`) instead of
  an intake edit to `.git/info/exclude`, which Claude Code protects and every E2E run was denied.

## 0.3.31 (2026-10-18)

- spec-agent: the wave-timing rule (set `finished_at` per handoff, write all four
  `metrics.waves` fields before landing or retry) moves into SKILL.md's Implement stage. In
  efficiency.md alone, a v0.3.30 run of sandbox ticket 003 left `task_minutes` and
  `wall_minutes` null.

## 0.3.30 (2026-10-18)

- spec-agent parallel waves, from the first subagent-mode run of sandbox ticket 003
  (`docs/e2e-runs.md`): wave dispatch passes the worktree as `Project root` plus a `Worktree:`
  line, since subagent tools may not take a working directory; wave metrics count first attempts
  only, so a blocked retry no longer drops `task_minutes` and `wall_minutes`. Refs #25.
- Sandbox ticket 003 and its eval case say the ticket sizes `small` and needs `resize standard`
  to reach a wave; the case also requires the wave timings.
- `evals.py`: a `state` check can test that a field is `present`.

## 0.3.29 (2026-10-18)

- E2E: sandbox tickets 001 and 002 run through `/work` in headless Claude Code and pass
  `evals.py check` on this commit, 001 twice and 002 three times
  ([docs/e2e-runs.md](docs/e2e-runs.md)). Fixes from five rounds:
  - A ticket that adds behavior creates its living-spec area when none exists. The spec
    template and the spec step say so; runs wrote `None.` while the rule was only in the
    analyst role.
  - Artifacts follow their templates' headings and columns, inline mode included (SKILL.md
    § Always and the verify step). Inline `verify.md` came out off-template.
  - An approval counts only for the gate it answers. One run took an earlier "unattended run"
    message as approval of its Deliver gate.
- `evals.py`'s `verify` check reads the `Result` column by its header instead of taking the last
  column.
- Harness honesty: README and docs/spec-agent.md say Codex, Antigravity CLI, and Cursor are best
  effort (roles share one session). Fallback reviewers read only the spec, the diff, and their
  role's inputs, and standard or large runs stop before review to suggest a fresh session
  (`review_context` in `state.json` and `retro.md`).
- docs/guardrails.md: known gaps of pattern hooks, and a recommended setup with read-only
  credentials and a sandbox for runs that touch infrastructure.
- docs/post-deliver.md: design for a `watch` stage after delivery (CI, review comments,
  post-merge verify, retro). The roadmap puts the metrics rollup first.
- README leads with spec-agent; install, plugins, per-harness details, and layout move to
  docs/install.md.
- Releases: PRs add a fragment in `changelog.d/` instead of editing `VERSION` and
  `CHANGELOG.md`. New `aicfg.py release` folds the fragments in, and `.github/workflows/release.yml`
  runs it on every merge to `main` and tags `vX.Y.Z`. `validate` checks fragments. PRs are
  squash-merged, and minor releases or spec-agent behavior changes need an eval run first
  (CONTRIBUTING.md § Releases). This is the last hand-edited version.

## 0.3.28 (2026-10-12)

- Living specs in spec-agent (#23, after OpenSpec): `specs/living/<area>.md` records how each
  capability area behaves now. The analyst reads the areas a ticket touches and writes the
  spec's new `## Requirement changes` section (ADDED, MODIFIED, REMOVED, or `None.`); the
  document stage applies it with `skills/spec-agent/scripts/living_specs.py`, which checks every
  block first and writes nothing on an unknown target or a duplicate. Each requirement names the
  run that last changed it. Checked on sandbox tickets 001 then 003: the second run modified a
  requirement the first added.

## 0.3.27 (2026-10-10)

- MCP servers sync (#21): `apply` merges `mcp/servers.toml` into `~/.claude.json`,
  `~/.codex/config.toml` (a marked block), and `~/.config/opencode/opencode.json` (new harness key
  `mcp`). `env_from` is written as a reference each harness expands (`${NAME}`, `env_vars`,
  `{env:NAME}`), never as a value. Only servers ai-config wrote are replaced or removed; a server
  you defined under the same name is reported as a conflict and left alone. `validate` checks the
  registry (and rejects an `env` table), `doctor` reports drift, and a disabled harness loses its
  servers. Checked with the real CLIs: Claude Code and OpenCode connect to a probe server and pass
  its variable; Codex lists it. Core's registry stays empty, so nothing changes until you add one.
- **[pack contract]** Packs may ship `mcp/servers.toml`; server names must start with the pack's
  `prefix`.

## 0.3.26 (2026-10-09)

- Cursor installs ai-config as a plugin (#50): `aicfg plugin` also writes
  `.cursor-plugin/plugin.json` (skills, agents, rules) and `.cursor-plugin/hooks.json`. Symlink a
  checkout to `~/.cursor/plugins/local/ai-config`. Core rules gain `alwaysApply: true`, which
  `validate` now requires.
- Cursor runs ai-config's guards: `overrides/cursor/hooks/guard.py` sends `beforeShellExecution`
  and `beforeReadFile` through the same Python guards, and asks become denials. `apply` links it
  to `~/.cursor/hooks/ai-config` and merges it into `~/.cursor/hooks.json` (`[cursor]` gains
  `hooks_dir` and `settings`; the merge now recognizes Cursor's flat hook entries). The manifest
  validates against Cursor's published schema; not yet run in a real Cursor.

## 0.3.25 (2026-10-09)

- OpenCode runs ai-config's guards (#50): `apply` links `overrides/opencode/plugin.js` to
  `~/.config/opencode/plugins/ai-config-guard.js` (new harness key `plugin`). It sends `bash`,
  `read`, `write`, `edit`, and `grep` calls through the same Python guards as Claude Code's hooks.
  OpenCode plugins can't prompt, so a call the guards would ask about is blocked, with the reason
  and "ask the user to run it themselves". MCP tools aren't guarded there yet. Checked inside
  OpenCode 1.18.35's runtime: the linked plugin loads and blocks `git push`.

## 0.3.24 (2026-10-09)

- An installed `aicfg` names itself in its hints: `doctor`'s fixes and the usage text say
  `aicfg <command>` instead of `python3 scripts/aicfg.py <command>`. A checkout is unchanged.

## 0.3.23 (2026-10-09)

- Packs install without a clone (#50): a pack entry may name `git = "<url>"` (and an optional
  `ref`: tag, branch, or commit) instead of `path`. `apply` fetches it once, shallow and
  detached, into `$AICFG_HOME/packs/<key>`; a failed fetch writes nothing. `status` only shows
  the FETCH, and `doctor` reports an unfetched pack. New `aicfg update` refetches every git pack
  at its `ref`, then applies, and leaves a clone with local changes alone. `path` packs are
  unchanged.

## 0.3.22 (2026-10-09)

- `aicfg` installs without a clone: `uv tool install git+https://github.com/bxker/ai-config` (or
  `pipx install`) gives an `aicfg` command with core's content bundled as `aicfg/_core` (#50).
  Installed, it keeps local files (`harnesses.local.toml`, `packs.local.toml`, `rules/*.local.md`)
  in `$AICFG_HOME` and never writes inside the package (a relative pack `path` is relative to
  `packs.local.toml`); `plugin` needs a checkout. A checkout
  works as before. New `pyproject.toml` (hatchling, build-time only); CI installs the package and
  validates its bundled core.

## 0.3.21 (2026-10-09)

- `aicfg` reports these problems instead of crashing with a traceback (found by the Rust port's
  parity runs): a dangling `*.md` link inside a skill (`validate`'s existing finding; `tokens`
  skips it); an invalid `overrides/<harness>/settings.fragment.json` (`status`/`apply` stop with
  nothing written, `doctor` lists it, `plugin` prints `ERROR`, `validate` reports it once); an
  unknown `agents_format` (a `doctor` finding). New hook events now merge in fragment order, not
  hash order, so `settings.json` is the same on every run.

## 0.3.20 (2026-10-09)

- `scripts/aicfg.py` is now the `aicfg/` package at the repo root: ten modules split along its old
  sections (`config`, `sources`, `opencode`, `plan`, `settings`, `plugin`, `tokens`, `validate`,
  `doctor`, `cli`), moved without rewriting. No behavior change: `python3 scripts/aicfg.py` still
  runs every command (it's a shim), with output identical to 0.3.19; `python3 -m aicfg` works
  too. Prepares per-harness adapters and an installable aicfg (#50).

## 0.3.19 (2026-10-09)

- OpenCode gets real subagents (#19; #50, step 4). OpenCode rejects Claude's agent frontmatter
  and stops loading its config, so `apply` renders each agent (core and packs) to
  `$AICFG_HOME/opencode/agents/` and links it from `~/.config/opencode/agents/`: `mode: subagent`,
  a permission `deny` for each tool the agent lacks, and no `model` (the caller's model is used).
  New `harnesses.toml` key `agents_format = "opencode"`; `doctor` flags stale renders. Verified
  with OpenCode 1.18.35: all 9 agents load as subagents with the expected denies.

## 0.3.18 (2026-10-08)

- Antigravity CLI, which replaced Gemini CLI, can install ai-config as a plugin: `agy plugin
  install https://github.com/bxker/ai-config` (#50, step 3). `aicfg plugin` also writes the root
  `plugin.json` it needs. Core rules start with `trigger: always_on` frontmatter, without which
  Antigravity drops them; `aicfg` strips it, so other harnesses get the same text, and `validate`
  requires it on core rules. No guard hooks for Antigravity yet. Built from public docs and
  issues; not yet run against a real `agy`.
- `aicfg` syncs to Antigravity (`~/.gemini/config/skills`, `~/.gemini/config/AGENTS.md`) in place
  of Gemini CLI. The `gemini` harness is kept disabled, so the next `apply` removes its old links;
  enable it in `harnesses.local.toml` if your account still runs Gemini CLI. Docs say Antigravity
  wherever they said Gemini.

## 0.3.17 (2026-10-08)

- Codex installs ai-config from the existing plugin: `codex plugin marketplace add
  bxker/ai-config`, then `codex plugin add ai-config@ai-config` (verified with Codex 0.161.0) (#50,
  step 2). Core's slash commands (`/work`, `/review`, `/spec-status`, `/spec-approve`,
  `/spec-resume`) are now user-invoked skills, because Codex skips commands that use `$ARGUMENTS`;
  they keep their names in Claude Code, and `apply` swaps the old command links for skill links.
  spec-agent reads `agents/` at the package root when an install drops the `roles` symlink.

## 0.3.16 (2026-10-08)

- **[pack contract]** `apply` renders rules and spec-agent extensions to `$AICFG_HOME`
  (default `~/.config/ai-config/`), outside the checkout, so packaged installs can read them
  (#50, step 1). Each harness's instructions link moves there on the next `apply`, and the old
  `dist/instructions.md` is removed. Non-breaking: `skills/spec-agent/references/extensions.md`
  is still written, but it's deprecated; packs that read it should read
  `$AICFG_HOME/extensions.md` instead. A later MINOR release stops writing it.

## 0.3.15 (2026-10-08)

- Docs: `docs/harness-packages.md` records the #50 spike: what each harness (Claude Code, Codex,
  Gemini CLI, OpenCode, Cursor) supports for native packages, rules, hooks, agents, and packs,
  with sources, unconfirmed items, and a proposed build order. The roadmap drops shipped items.

## 0.3.14 (2026-10-07)

- Claude Code plugin: `/plugin marketplace add bxker/ai-config`, then
  `/plugin install ai-config@ai-config`, installs the skills, agents, commands, and guard hooks
  without `aicfg`. Rules, packs, and other harnesses still need `aicfg`. `aicfg plugin` generates
  `.claude-plugin/` from the repo, and `validate` fails when it's stale, so run it after every
  `VERSION` bump. Packs stay `aicfg` packs (decision in `docs/packs.md`) (#26).

## 0.3.13 (2026-10-07)

- spec-agent: in subagent mode, independent plan tasks (no `after:` dependency, no shared
  files) run as parallel waves in separate git worktrees and land in plan order; at most 2
  per wave for `standard`, 3 for `large`. State and the retro record the time saved. Sandbox
  ticket 003 and `evals/cases/sandbox-003.toml` exercise it (#25).
- spec-agent: gates are asked as a multiple-choice question (Approve / Request changes, plus
  any open choices) when the harness has one, e.g. Claude Code's `AskUserQuestion`.

## 0.3.12 (2026-10-07)

- Supported platforms documented: macOS and Linux, Windows through WSL or with symlinks
  enabled. `skills/spec-agent/roles` stays a symlink; `validate` and `doctor` now say when a
  checkout broke it and how to restore it (#11).

## 0.3.11 (2026-10-07)

- **[pack contract]** `validate` enforces always-loaded token budgets (rules plus descriptions)
  per source: 3,000 for core, and a pack's optional `max_always_tokens` in `pack.toml`.
  Non-breaking: a pack without the key gets a warning above 1,000 tokens, and any description
  over 100 tokens gets a warning. `tokens` shows each source against its budget (#10).
- `unslop`: the rule catalogue moves word for word into `references/`, so SKILL.md is ~1.5k
  tokens instead of ~3.5k, with a 60-token description. `doc-types` description trimmed.

## 0.3.10 (2026-10-07)

- spec-agent, from the #39, #12, #17, and #42 retros (#44): the verifier runs anything a person
  runs once for real, with a fresh fake `HOME`; the implementer shows red by switching off only
  the new change; the done checkpoint is pushed after CI on the delivered commit finishes; test
  lines count about half toward size.

## 0.3.9 (2026-10-07)

- `apply` removes ai-config's hooks from a disabled harness's settings file (other hooks and
  settings stay, backup first), and `doctor` reports them until it does. Uninstalling no longer
  needs a manual step (#42).

## 0.3.8 (2026-10-07)

- Docs: `docs/troubleshooting.md`, by symptom: missing items, `CONFLICT`, pack errors, settings
  backups, uninstalling, and reporting a guard hook mistake. `doctor` points to it when it finds
  a problem (#17).

## 0.3.7 (2026-10-06)

- `aicfg doctor`: a read-only check of this machine's install. It reports stale renders,
  missing, wrong, stale, or broken links, broken or incompatible packs, unmerged hooks, and
  harnesses that aren't installed, each with its fix, and exits 1 on any problem (#12).
- `aicfg` on Python older than 3.11 prints one line saying so instead of a traceback.

## 0.3.6 (2026-10-06)

- Sandbox fixes from the first E2E run (#18): a `.gitignore` so setup and test runs leave a clean
  tree, and a decoy `.env` that the new `canary` eval check proves never leaked. `sandbox-002`
  uses it. The `main_untouched` check's PASS message no longer reads "expected".

## 0.3.5 (2026-10-06)

- `scripts/evals.py`: `check` grades a finished spec-agent run against a case file (two sandbox
  cases included), and `triggers` scores skill selection from descriptions with any model CLI.
  Packs can add their own cases. Offline tests run in CI (#6).

## 0.3.4 (2026-10-06)

- Docs: `CONTRIBUTING.md` covers setup, the change workflow, and spec-agent use. The rules stay
  in `AGENTS.md`, linked both ways (#15).

## 0.3.3 (2026-10-06)

- Docs: `docs/tutorial.md` builds a pack with one domain skill from a fresh clone, linked from
  the README. Every command in it is checked by running the tutorial itself (#13).

## 0.3.2 (2026-10-05)

- Docs: `docs/architecture.md` with one diagram, an install-time vs run-time table, and a
  glossary, linked from the README (#14).

## 0.3.1 (2026-10-05)

- spec-agent, from the first five run retros (#33): sizing counts changed lines, not just
  files; intake warns about other open PRs that bump `VERSION`; intake names `fallback` mode
  and how to install the agents; the Deliver gate lists code changes before spec artifacts;
  gates record when they were presented and approved so retros split agent time from waits;
  `code-reviewer` checks user-facing text against the docs.

## 0.3.0 (2026-10-05)

- **[pack contract]** Ticket connector contract in `skills/spec-agent/references/connectors.md`.
  `validate` fails when a connector (a core `ticket-*` skill or a pack's
  `[extensions.ticket].connector`) has no `##` heading for `fetch`, `comment`, `transition`,
  or `link_pr`. Packs: check your connector, and update `requires_core` to `">=0.3, <0.4"`.
- Packs keep one ticket connector each, now documented.
- `ticket-github` works through the GitHub MCP server when `gh` isn't available.

## 0.2.1 (2026-10-05)

- **[pack contract]** `ticket-jira`: `review_status`, `in_progress_status`, and `blocked_status`
  accept a table keyed by project key, with an optional `"*"` fallback (#4). Non-breaking: a
  plain status name still works.
- `ticket-jira`: task-list checkboxes post to Jira as escaped text, so use ✅ / ⬜ bullets (#4).
- Docs: README states per-harness support, stale Jira and machine-specific notes removed.

## 0.2.0 (2026-10-05)

- **[pack contract]** Rule order: core rules first, then each pack's rules as a labelled block
  in `packs.toml` order, then `*.local.md` rules under their own label. Pack rules no longer
  interleave with core rules by filename. Packs: re-check your rules read correctly after
  core's, and update `requires_core` to `">=0.2, <0.3"`.
- `validate` fails when the newest CHANGELOG heading doesn't match `VERSION`, or when an
  `## Unreleased` section exists.

## 0.1.1 (2026-10-05)

- `doc-types` skill: classify a doc as one Divio type (tutorial, how-to, reference,
  explanation), write to that type's shape, and split mixed docs. `doc-writer` and `runbook`
  use it.
- Example pack in `examples/pack-acme`, validated by a test and in CI.

## 0.1.0 (2026-10-05)

First versioned release. All entries but the first shipped before versioning began.

- **[pack contract]** `VERSION` file and `requires_core` in `pack.toml`. `validate` fails and
  `apply` writes nothing when core doesn't satisfy a pack. Packs without it get a warning.
- Unslop and runbook skills, and two honesty rules.
- `ticket-jira` connector and spec-agent campaign mode.
- **[pack contract]** Packs: layered source repos with prefixes, collision checks, hook
  fragments, tripwires, `validate --pack`, and spec-agent extensions (`domains`,
  `intake_context`, `ticket`, `deliver_checks`).
- `aicfg tokens`.
- Core hardening: guard hook bypasses closed, wider secret coverage, hermetic `aicfg` tests,
  CI actions pinned to SHAs.
- spec-agent: 9 agents, domain skills for the DevOps stack, ticket connectors (local,
  GitHub), checkpoint commits at every stop, retro-driven improvements.
- Claude guard hooks and settings merge, validation with cross-references, and tests.
