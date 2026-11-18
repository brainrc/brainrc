<!-- divio: how-to -->
# Turn a Claude Code plugin into a pack

Move a Claude Code plugin of your own into a pack, so every tool brainrc manages gets its skills,
agents, commands and MCP servers, and Claude Code keeps its hooks.

## 1. Import it

Name the plugin's folder, the one that holds `.claude-plugin/plugin.json`:

```bash
brainrc import ~/src/shipit --name acme --to ~/src/acme-ai-pack --dry-run   # what it would write
brainrc import ~/src/shipit --name acme --to ~/src/acme-ai-pack
```

| In the plugin | In the pack |
|---|---|
| `skills/<name>/` | `skills/acme-<name>/`, every file in it, with `name:` changed to match |
| `agents/<name>.md` | `agents/acme-<name>.md`, with `name:` changed to match |
| `commands/<name>.md` | `commands/acme-<name>.md` |
| `hooks/hooks.json` and the scripts its hooks run | `overrides/claude/settings.fragment.json` and `overrides/claude/hooks/` |
| `.mcp.json` | `mcp/servers.toml`, each server named `acme-<name>` |

Every item name starts with the pack's prefix ([naming](../packs.md#naming)). A plugin's skills
were called `/shipit:name`; `import` changes `shipit:name`, `[agent: name]` and "`name` skill" in
the items' text to the new names. Each item keeps the rest of its frontmatter and a comment
naming the file and lines it came from.

## 2. Check what it couldn't move

`import` prints a `WARN` line for each of these, and leaves them out:

- **A value in a server's `env`.** brainrc writes variable names, never values. An `env` entry of
  `"${TOKEN}"` becomes `env_from = ["TOKEN"]`; set any other in your environment and add its
  name to `env_from` ([MCP servers](../formats.md#mcp-servers-mcpserverstoml)).
- **A server that runs the plugin's own files** (`${CLAUDE_PLUGIN_ROOT}` in its command): install
  them somewhere, then add the server to `mcp/servers.toml` by hand.
- **A link** inside a skill: copy what it points at into the skill.

In `settings.fragment.json`, `${CLAUDE_PLUGIN_ROOT}/hooks/x` became `{{hooks_dir}}/x`, which
`apply` fills in ([layout](../packs.md#layout)). Test each hook with `brainrc.testing` in the
pack's `tests/` ([pack tests](../packs.md#pack-tests));
[examples/pack-homelab](../../examples/pack-homelab/README.md) has one.

## 3. Validate, then stop installing the plugin

`import` checks the pack as `validate --pack` does. The pack it writes is only the plugin's items:
for the rest of what a pack carries (a README, tripwires, tests, CI), start one with
`brainrc new pack acme` and move the imported items into it.

```bash
brainrc validate --pack ~/src/acme-ai-pack
```

Turn the pack on ([use a pack](use-a-pack.md)), then uninstall the plugin from Claude Code, so
its skills and hooks don't load twice.
