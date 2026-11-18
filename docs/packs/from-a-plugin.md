<!-- divio: how-to -->
# Turn a Claude Code plugin into a pack

Move a Claude Code plugin of your own into a pack, so every tool brainrc manages gets its skills,
agents and MCP servers, and its instructions can become rules.

## 1. Start a pack

```bash
brainrc new pack acme --to ~/src/acme-ai-pack
```

## 2. Move each part

| In the plugin | In the pack |
|---|---|
| `skills/<name>/SKILL.md` | `skills/acme-<name>/SKILL.md`, with `name:` changed to match |
| `agents/<name>.md` | `agents/acme-<name>.md`, with `name:` changed to match |
| `commands/<name>.md` | `commands/acme-<name>.md` |
| `hooks/hooks.json` and its scripts | `overrides/claude/settings.fragment.json` and `overrides/claude/hooks/` |
| `.mcp.json` | `mcp/servers.toml` |
| `.claude-plugin/plugin.json` | `pack.toml` (name, description) |

Every item name starts with the pack's prefix ([naming](../packs.md#naming)). A plugin's skills
were called `/plugin:name`; in the pack they are `/acme-name`, so update any text that names them.

## 3. Rewrite the hook commands

In `settings.fragment.json`, keep the plugin's `hooks` object as it was, and replace
`${CLAUDE_PLUGIN_ROOT}/hooks` with `{{hooks_dir}}`, which `apply` fills in
([layout](../packs.md#layout)). Test each hook with `brainrc.testing` in the pack's `tests/`
([pack tests](../packs.md#pack-tests)); [examples/pack-homelab](../../examples/pack-homelab/README.md)
has one.

## 4. Rewrite the MCP servers

Each server in `.mcp.json` becomes a `[servers.<name>]` table. Name the variables a server needs
in `env_from`, never their values ([MCP servers](../formats.md#mcp-servers-mcpserverstoml)):

```toml
[servers.acme-docs]
command = "npx"
args = ["-y", "@acme/docs-mcp"]
env_from = ["ACME_TOKEN"]
```

## 5. Validate, then stop installing the plugin

```bash
brainrc validate --pack ~/src/acme-ai-pack
```

Turn the pack on ([use a pack](use-a-pack.md)), then uninstall the plugin from Claude Code, so
its skills and hooks don't load twice.
