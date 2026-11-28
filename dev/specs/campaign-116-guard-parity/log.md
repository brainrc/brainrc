# Campaign gh:116 · guard parity across tools (E11)

## 2026-11-26T03:40:00Z · engine · Campaign gate · dry run
`/brainrc-work --campaign gh:116 --shape ordered --dry-run`, worked by hand: the skill ships in
brainrc/gatework, which isn't installed in the build environment.

- Members: #155 (Cursor), #156 (OpenCode), #157 (Codex), #158 (Antigravity), #322 (compile guard
  rules into OS sandbox settings). #323 (the security-baseline pack) is skipped: the brief leaves it
  out.
- Shape: `ordered`. Dependency source: `none`. #155 comes first because it moves the shared
  plumbing (`guard_bridge.py`, `tests/guard_cases.py`) the other evaluators reuse; #322 stands alone.
- Delivery: one draft PR with one commit per child, since only one branch is pushable here.
- Starts from `main` after #387 (E10) merged as ed6debb, checked on GitHub.

## engine · Campaign gate · approved
The coordinator's brief passes on the maintainer's "Yes, merge and start" to its question about
merging #387 and building the four evaluators and the sandbox compile as draft PRs, leaving #323
out. Recorded as approved on that basis; per-child Spec and Plan are logged here. Merging stays
with the maintainer.

## engine · shared · Spec and Plan
- Every tool's guard runs core's Claude Code guards through `overrides/claude/hooks/guard_bridge.py`,
  passing where the command runs, so a pack's `[[guard.deny]]` and `[[guard.ask]]` apply under its
  `[scope]` the same way everywhere. A pack deny wins over any ask. A tool that can't ask blocks an
  ask and tells the model to ask the user to run it.
- `tests/guard_cases.py` holds the acme cases (19 wrapped denies, 8 near misses, deny over ask, a
  missing or broken rules file); each tool's test class mixes them in.

## engine · gh:155 · Spec and Plan
- Cursor's `beforeShellExecution` and `beforeReadFile` hook runs core's guards through the bridge,
  with the event's `cwd` (else the first workspace root) as where. Cursor's ask is unreliable for
  shell commands, so an ask denies with the reason.
- Plan: `overrides/cursor/hooks/guard.py`, `guard_bridge.py` (new), tests in `tests/test_hooks.py`.

## engine · gh:156 · Spec and Plan
- OpenCode's plugin passes the session `directory`, joined with a command's `workdir`, as where.
  A plugin can't ask, so an ask throws with the reason and the run-it-yourself line.
- Plan: `overrides/opencode/plugin.js`, tests in `tests/test_hooks.py`.

## engine · gh:157 · Spec and Plan
- Codex reads PreToolUse hooks from `$CODEX_HOME/hooks.json`, in Claude Code's shape. Its hook gets
  `Bash`, `apply_patch` (the patch in `tool_input.command`) and `mcp__*` calls; only allow and
  deny work, an ask counts as a failed hook and the call runs, so the hook maps ask to deny. The
  patch's added files and lines go to the secrets guard as a Write.
- `harnesses.toml` gains Codex's `hooks_dir` and `settings`. Codex asks the user to trust new hooks
  once in `/hooks`; the docs say so.
- Plan: `overrides/codex/hooks/guard.py` and `settings.fragment.json` (new), harnesses.toml,
  tests in `tests/test_hooks.py` and `tests/test_brainrc.py`.

## engine · gh:158 · Spec and Plan
- Antigravity reads `~/.gemini/config/hooks.json`, where each hook set sits under a name. brainrc's
  goes under `brainrc`, through a new `settings_format = "antigravity"` in harnesses.toml that
  maps the file to Claude Code's shape and back, so merge, ownership, doctor and uninstall reuse
  the same code. An unknown format is a config error in apply and doctor.
- The hook guards `run_command` (`CommandLine`, `Cwd`, else the first workspace path). A deny
  replies `deny`, an ask `force_ask`, and no objection `allow`, which Antigravity's docs say passes
  the decision on to the next hook or the default policy, so it doesn't widen what runs.
- Plan: `overrides/antigravity/hooks/guard.py` and `settings.fragment.json` (new), harnesses.toml,
  `brainrc/config.py`, `plan.py`, `settings.py`, `doctor.py`, `uninstall.py`, `cli.py`, the
  harnesses schema; tests in `tests/test_hooks.py` and `tests/test_brainrc.py`.

## engine · gh:322 · Spec and Plan
- A `[[guard.deny]]` can set `path` (starting `~/` or `/`) or `host` (a domain, optionally `*.`)
  in place of `match` or `tool`. apply compiles them into Claude Code's
  `sandbox.filesystem.denyRead` and `denyWrite` and `sandbox.network.deniedDomains`, and records
  the entries it adds in `settings-owned.json`, as #142 does for permissions: the user's stay, and
  exactly the pack's go when it's disabled or brainrc is uninstalled.
- The sandbox can't ask and doesn't know where a command runs, so validate refuses a path or host
  rule under `[[guard.ask]]` and one a scoped pack leaves scoped (`scope = {}` says everywhere).
- Plan: `brainrc/guard.py` (`sandbox()`), `settings.py`, `plan.py`, the pack.toml schema,
  docs/packs.md and docs/guardrails.md; tests in `tests/test_guard_rules.py` and
  `tests/test_pack_settings_keys.py`.

## engine · gaps left open
- Antigravity's hook covers `run_command` only: its file tools' argument names and MCP tool naming
  aren't documented. (OpenCode's MCP gap, listed here first, closed in the real-run pass below.)
- Cursor and Antigravity haven't run for real (see the real-run pass below).
- The sandbox covers Bash and its child processes, not Claude Code's Read tool or web fetches, and
  takes effect only with `sandbox.enabled` on. Other tools have no sandbox settings brainrc writes.
- Nothing here needs brainrc/gatework.

## review · code-review (high) on PR #388, 7 of 8 findings fixed in one commit
- gh:157: a command sent as an argv list skipped the guards (an `apply_patch` list lost its
  newlines); lists are joined, and the patch is read from its last string.
- gh:158: doctor crashed on a disabled harness's unknown `settings_format`, since plan reads
  disabled ones too; it checks them all now. A `brainrc` entry that isn't an object was reported
  as invalid JSON; apply, doctor and uninstall now say what's wrong. uninstall fell back to
  Claude's shape on an unknown format and left Antigravity's hooks silently; it says so now.
- gh:322: a `host` with a trailing newline passed validate (`$` before a final newline); it uses
  a full match. The minimal profile wrote sandbox entries; they follow the hooks profile now, as
  a pack's permissions do. Only the first fragment's `sandbox` table was kept; every fragment's
  lists are joined now.
- Not changed: an empty sandbox list the user had before brainrc added to it goes with brainrc's
  entries, as #142's permission lists do; keeping it needs settings-owned.json to record what was
  there first, for permissions and sandbox alike.

## verify · real harness runs, asked for after PR #388
- Codex CLI 0.172 and OpenCode 1.19.6, installed from npm on a scratch machine, ran real sessions
  against a local mock model that called the tools, with the acme pack applied to a scratch home
  and two repos (an acme remote, a personal one).
- Codex, for real: shell (plain, `bash -c`, `sudo -E env`, `&&`), `apply_patch` (gpt-5.5's
  freeform tool) and code mode (`exec` calling `tools.exec_command`) gave the expected deny or run
  in each repo. Untrusted hooks are skipped silently in `codex exec`; trusting them in the TUI's
  review screen fixed that.
- Bug, fixed: Codex names an MCP server's tools with `-` turned into `_` (`mcp__acme_jira__…`), so
  the pack's `mcp__acme-jira__*` rule never matched. Rules now match either spelling.
- Bug, fixed: Codex appends ". Command: …" to a deny reason, which doubled our full stop.
- OpenCode, for real: bash (with `workdir`), read and secrets gave the expected results. Bug,
  fixed: MCP tools (`acme-jira_get_transitions`) ran unguarded. The plugin now asks OpenCode's
  client which servers are connected, matches the longest name, and sends
  `mcp__<server>__<tool>` to the guard; the real run then blocked the pack's ask and core's
  write-verb ask, and let reads through.
- Cursor and Antigravity have no CLI that runs here without a sign-in, so a script read the hooks
  files `apply` wrote, sent each hook a full payload shaped like the documented input, and ran the
  command only when the reply allowed it. Every case matched the design. Antigravity's
  `view_file` of `.env` isn't checked, the known gap above.
