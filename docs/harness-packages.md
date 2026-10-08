# Harness packages

What each harness supports for installing ai-config as a native package, without a clone.
Research for [#50](https://github.com/bxker/ai-config/issues/50), done 2026-10-08. Formats
change fast: re-check a harness's docs before building its package.

## At a glance

| Harness | Package and install | Rules without a clone | Hooks | Agents | Packs |
|---|---|---|---|---|---|
| Claude Code | `.claude-plugin/` ([shipped](../README.md#claude-code-plugin-no-clone)); `/plugin install` | `SessionStart` hook output (10,000-char cap) | yes: allow, ask, deny | yes, as `ai-config:<name>` | plugin `dependencies` with semver ranges |
| Codex | `.codex-plugin/` **or `.claude-plugin/`** (verified); `codex plugin marketplace add owner/repo` | no plugin route: `~/.codex/AGENTS.md` or config `developer_instructions` | yes: `PreToolUse`, `SessionStart` | TOML roles in config; not shippable in a plugin | separate plugin; no dependencies found |
| Gemini CLI | `gemini-extension.json`; `gemini extensions install <git url>` | the extension's `GEMINI.md` (`contextFileName`) | yes: `BeforeTool` can deny; ask undocumented | markdown, `agents/` (preview) | separate extension; no dependencies |
| OpenCode | JS plugin (npm or `~/.config/opencode/plugins/`): hooks and tools only | `instructions[]` config or `AGENTS.md` | blocks by throwing; no ask | markdown files with a different frontmatter | `plugin[]`, `instructions[]`, `skills.paths` |
| Cursor | `.cursor-plugin/plugin.json`: rules, skills, agents, commands, hooks | through the plugin | yes: allow, deny; ask reported broken | markdown | marketplace JSON (schema unconfirmed) |

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

## Gemini CLI

Sources: [extensions reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md),
[custom commands](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/custom-commands.md),
[skills](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md),
[hooks](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/reference.md),
[subagents](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md).

- An extension ships `GEMINI.md` (always loaded), `skills/`, `commands/*.toml` (`prompt`,
  `{{args}}`), `agents/`, and `hooks/hooks.json` with `${extensionPath}`.
- Hooks block with exit code 2 or `decision: "deny"`; non-JSON stdout means allow, so a guard
  must never print stray output. Ask: **undocumented**.
- Agents: `model: haiku|sonnet|opus` needs mapping to Gemini models.

## OpenCode

Source: [sst/opencode](https://github.com/sst/opencode) docs source at `a697115` (the docs site
was blocked here): `packages/web/src/content/docs/`.

- A plugin is a JS module: hooks (`tool.execute.before`), tools, and system-prompt transforms. It
  can't ship agent, skill, or command files, so the package is a config dir plus a small plugin.
- Agents need a transform ([#19](https://github.com/bxker/ai-config/issues/19)): Claude's
  `tools: Read, Grep` fails OpenCode's schema (it wants a boolean map, or `permission`), `model`
  must be `provider/model-id`, and `mode: subagent` is required.
- Skills: native, `~/.config/opencode/skills/` (also reads `~/.claude/skills/`).

## Cursor

Evidence is weakest here: cursor.com was blocked, so claims come from search-result excerpts of
[cursor.com/docs](https://cursor.com/docs/plugins) and the Cursor forum.

- Plugins (Cursor 2.5+): `.cursor-plugin/plugin.json` can bundle rules, skills, agents, commands,
  MCP, and hooks. Marketplace schema and local-plugin reliability are **unconfirmed**.
- Hooks: `hooks.json` with camelCase events (`beforeShellExecution`, `preToolUse`); Claude's
  PascalCase format is rejected. `permission: ask` was reported broken in 2.4.21.

## What this means

1. **One generated `.claude-plugin/` may serve Claude Code, Codex, and (close) Cursor.** Gemini
   needs `gemini-extension.json`; OpenCode needs a config dir plus a JS hook plugin.
2. **Commands should become skills**, or be generated per harness: Codex skips `$ARGUMENTS`
   commands and Gemini wants TOML.
3. **Rules and pack extensions need rendering outside the checkout** (`$AICFG_HOME`), then each
   harness loads them its own way. Codex plugins have no rules route yet.
4. **Guard hooks need a deny fallback**: only Claude Code reliably supports ask.

## Proposed order for #50

1. Render to `$AICFG_HOME`; spec-agent reads extensions from there (every harness needs it).
2. Codex through the existing `.claude-plugin/`: test the install, convert commands to skills.
3. Gemini extension: manifest, `GEMINI.md`, TOML commands, hooks with deny.
4. OpenCode: config dir, agent transform (#19), JS guard plugin.
5. Cursor: after confirming the format against its docs.
6. Packs as packages, starting with Claude `dependencies`.
