# Harness packages

What each harness supports for installing ai-config as a native package, without a clone.
Research for [#50](https://github.com/bxker/ai-config/issues/50), done 2026-10-08. Formats
change fast: re-check a harness's docs before building its package. Gemini CLI was retired for
consumer accounts on 2026-06-18; [Antigravity CLI](#antigravity-cli) replaced it.

## At a glance

| Harness | Package and install | Rules without a clone | Hooks | Agents | Packs |
|---|---|---|---|---|---|
| Claude Code | `.claude-plugin/` ([shipped](install.md#claude-code)); `/plugin install` | `SessionStart` hook output (10,000-char cap) | yes: allow, ask, deny | yes, as `ai-config:<name>` | plugin `dependencies` with semver ranges |
| Codex | `.codex-plugin/` **or `.claude-plugin/`** (verified); `codex plugin marketplace add owner/repo` | no plugin route: `~/.codex/AGENTS.md` or config `developer_instructions` | yes: `PreToolUse`, `SessionStart` | TOML roles in config; not shippable in a plugin | separate plugin; no dependencies found |
| Antigravity CLI | root `plugin.json` ([shipped](install.md#antigravity-cli), unverified); `agy plugin install <git url>` | plugin `rules/*.md` with `trigger:` frontmatter | yes: `PreToolUse` ask or deny; no known "no opinion" reply | markdown, `agents/` | separate plugin; no dependencies found |
| OpenCode | JS plugin (npm or `~/.config/opencode/plugins/`): hooks and tools only | `instructions[]` config or `AGENTS.md` | blocks by throwing; no ask | markdown files with a different frontmatter | `plugin[]`, `instructions[]`, `skills.paths` |
| Cursor | `.cursor-plugin/plugin.json` ([shipped](install.md#cursor), unverified); symlink a checkout to `~/.cursor/plugins/local/` | plugin `rules/` with `alwaysApply: true` | yes: allow, deny; ask reported broken | markdown, `agents/` | separate plugin; a `.cursor-plugin/marketplace.json` lists several |

## Claude Code

Sources: [hooks](https://code.claude.com/docs/en/hooks.md),
[plugin components](https://code.claude.com/docs/en/plugins/components.md),
[dependencies](https://code.claude.com/docs/en/plugins/dependencies.md),
[plugin CLI](https://code.claude.com/docs/en/plugins/cli-reference.md).

- Rules: a plugin `SessionStart` hook's stdout, or `hookSpecificOutput.additionalContext`, is
  added to context. Matchers `startup|resume|clear|compact` re-inject after `/clear` and
  compaction. Over 10,000 characters, Claude sees a 2,000-character preview only. A plugin-root
  `CLAUDE.md`, rules, and most settings are not loaded. `claude plugin validate` accepts the hook
  (checked here); that the text reaches the model is **unconfirmed** (needs a live session).
- Packs: `"dependencies": [{"name": "ai-config", "version": "^0.3"}]` installs core with a pack;
  versions resolve to git tags `<plugin>--v<version>`. `claude plugin list --json` lists installed
  plugins with their paths. A pack skill dispatching a core agent across plugins is **unconfirmed**.
- Hooks from several plugins all run; `deny` > `ask` > `allow`.

## Codex

Source: [openai/codex](https://github.com/openai/codex) at `529cd6b` (the docs site was blocked
here): `codex-rs/core-plugins/`, `codex-rs/hooks/`, `codex-rs/agent-roles/`.

- Reads `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json` as well as its own
  `.codex-plugin/`. **Verified** with Codex 0.161.0: `codex plugin marketplace add <repo>` and
  `codex plugin add ai-config@ai-config` install our plugin unchanged. The install copy **drops
  symlinks** (`skills/spec-agent/roles`), so spec-agent falls back to `../../agents/`.
- Skills: native, `~/.agents/skills` (`~/.codex/skills` deprecated). Custom prompts are deprecated
  for skills; a plugin's `commands/` become skills, **except any that use `$ARGUMENTS`** (verified:
  all five of ours were skipped). Core now ships them as user-invoked skills, which Codex installs.
- Hooks: `PreToolUse`, `SessionStart`, and more, from a plugin's `hooks/hooks.json`. Whether a
  `SessionStart` hook can inject rules is **unconfirmed**.
- Agents: `[agents.<role>]` TOML; a plugin can't ship them.

## Antigravity CLI

Google's docs site was blocked here and `agy` (closed source) couldn't be installed, so this
comes from public sources: the [antigravity-cli](https://github.com/google-antigravity/antigravity-cli)
CHANGELOG and issues (#403, #1053, #1059), and plugins that record tested behavior
([MemPalace](https://github.com/MemPalace/mempalace/blob/develop/hooks/antigravity/INVESTIGATION.md),
[CoalHearth v2.8.0](https://github.com/TheColliery/CoalHearth/releases/tag/v2.8.0) on agy 1.3.1).
Nothing here was run against a real `agy`.

- A plugin is a folder with `plugin.json` (`name` only; extra keys may be rejected), plus optional
  `skills/`, `agents/`, `rules/`, `hooks.json`, and `mcp_config.json`. `agy plugin install <git
  url>` needs `plugin.json` at the repo root. No `commands/`: skills are the slash commands.
  Install may copy only the folders it recognises (#403).
- Rules: `rules/*.md` load only with frontmatter naming a `trigger` (`always_on`,
  `model_decision`, `glob`, `manual`); files without one are dropped silently.
- Hooks: `hooks.json` at the plugin root, `{"<name>": {"PreToolUse": [{"matcher", "hooks"}]}}`;
  commands run from the plugin folder. `PreToolUse` gets `toolCall: {name, args}` (`run_command`
  → `args.CommandLine`; `view_file`, `write_to_file`, `replace_file_content`) and prints
  `{"decision": "ask" | "deny", "reason"}`. An empty `{}` is reported to deny every call and
  `allow` is documented as auto-approve, so a guard has no safe reply for "no objection". **Not
  shipped** until a live test settles it.
- Skills: `disable-slash-command` hides a skill from `/`; `disable-model-invocation` is likely ignored.

## OpenCode

Source: [sst/opencode](https://github.com/sst/opencode) docs source at `a697115` (the docs site
was blocked here): `packages/web/src/content/docs/`.

- A plugin is a JS module: hooks (`tool.execute.before`), tools, and system-prompt transforms. It
  can't ship agent, skill, or command files, so the package is a config dir plus a small plugin.
- Agents need a transform ([#19](https://github.com/bxker/ai-config/issues/19), shipped in 0.3.19):
  Claude's `tools: Read, Grep` makes OpenCode's whole config invalid (verified, 1.18.35); it wants
  `permission`, `model` as `provider/model-id`, and `mode: subagent`.
- Guard plugin: `tool.execute.before` can block by throwing and `permission.ask` can answer a
  prompt OpenCode already shows, but a plugin can't force a prompt, so "ask" becomes "deny".
- Skills: native, `~/.config/opencode/skills/` (also reads `~/.claude/skills/`).

## Cursor

cursor.com is blocked from where this was built, so the format comes from Cursor's official
plugin repo, [cursor/plugins](https://github.com/cursor/plugins) (checked 2026-10-09 at `ccb5507`:
`schemas/`, its plugins, and its `create-plugin` scaffold skill), plus hook payload types from the
community [`cursor-hooks`](https://www.npmjs.com/package/cursor-hooks) package.

- Manifest: `.cursor-plugin/plugin.json`, only `name` required, unknown keys rejected. `skills`,
  `agents`, `rules`, `commands` take relative paths; `hooks` a path or an inline object. Our
  generated manifest validates against `schemas/plugin.schema.json`.
- Local install: a plugin directory, or a symlink to one, at `~/.cursor/plugins/local/<name>/`.
  A search result says Cursor falls back to `.claude-plugin/` when `.cursor-plugin/` is missing,
  so we ship our own: Cursor rejects Claude's hook format.
- Rules: `description`, `alwaysApply`, optional `globs` frontmatter; Cursor's examples use `.mdc`.
  Whether a plugin loads `.md` rules is **unconfirmed**.
- Agents: `name`, `description`, `model`, `readonly`. Whether Cursor accepts our `model: sonnet`
  values is **unconfirmed**.
- Hooks: `{"version": 1, "hooks": {"<event>": [{"command": ...}]}}`, user file
  `~/.cursor/hooks.json`, `${CURSOR_PLUGIN_ROOT}` in plugin hooks. `beforeShellExecution` gets
  `{command}`, `beforeReadFile` `{file_path, content}`; the reply is `{permission, user_message,
  agent_message}`. `permission: ask` was reported broken in 2.4.21 and reads take only allow or deny.

## What this means

1. **One generated `.claude-plugin/` serves Claude Code and Codex; Cursor gets `.cursor-plugin/`.**
   Antigravity needs a root `plugin.json`; OpenCode needs a config dir plus a JS hook plugin.
2. **Commands should become skills**, or be generated per harness: Codex skips `$ARGUMENTS`
   commands and Antigravity has no commands.
3. **Rules and pack extensions need rendering outside the checkout** (`$AICFG_HOME`), then each
   harness loads them its own way. Codex plugins have no rules route yet.
4. **Guard hooks need a deny fallback**: only Claude Code reliably supports ask.

## Proposed order for #50

1. Render to `$AICFG_HOME`; spec-agent reads extensions from there (every harness needs it).
2. Codex through the existing `.claude-plugin/`: test the install, convert commands to skills.
3. Antigravity plugin: root `plugin.json`, rule triggers (done, unverified); hooks after a live test.
4. OpenCode: agent transform (#19, done); guard plugin (deny only) done in 0.3.25.
5. Cursor: `.cursor-plugin/` plugin and guard hooks (deny only) done in 0.3.26; unverified in a real Cursor.
6. Installable `aicfg` (`uv tool install` or `pipx install` from GitHub, core bundled): done in
   0.3.22. Packs by git URL, fetched by `aicfg` (`git` + `ref`, `aicfg update`): done in 0.3.23.
