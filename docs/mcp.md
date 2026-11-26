# MCP servers

A pack can define MCP servers once, in `mcp/servers.toml`, and `apply` writes them into each
tool's own config. brainrc core ships none; they come from your packs. Only the `full` profile
installs them, and `full` is the default ([configuration](configuration.md#brainrclocaltoml)).

## Add a server

In your pack's `mcp/servers.toml`:

```toml
[servers.acme-github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env_from = ["GITHUB_PERSONAL_ACCESS_TOKEN"]   # names only; the value stays in your environment
harnesses = ["claude", "codex"]               # optional; default: every tool brainrc writes MCP servers for

[servers.acme-docs]
url = "https://docs.example.com/mcp"          # an HTTP server instead of a command
```

A server's name starts with the pack's prefix, like its other items. Then run `brainrc apply`.
Close Claude Code first: it rewrites `~/.claude.json` while it runs, and `apply` refuses to write a
file that changed under it.

## Where they go

| Tool | File | Written as |
|---|---|---|
| Claude Code | `~/.claude.json` | `mcpServers` |
| Codex | `~/.codex/config.toml` | a marked `[mcp_servers]` block |
| OpenCode | `~/.config/opencode/opencode.json` | `mcp` (`opencode.jsonc` when only that exists, keeping its comments) |
| GitHub Copilot | `~/.copilot/mcp-config.json` | `mcpServers`, each with `tools: ["*"]` |
| Devin Local | `~/.config/devin/mcp_config.json` | `mcpServers`; variables as `${env:NAME}` |
| Kiro | `~/.kiro/settings/mcp.json` | `mcpServers`; Kiro expands `${NAME}` only for variables in its approved list |
| Amp | `~/.config/amp/settings.json` | `amp.mcpServers` (`settings.jsonc` when only that exists) |
| JetBrains Junie | `~/.junie/mcp/mcp.json` | `mcpServers`, with no `env`: Junie reads no variable references, so the server gets them from the environment Junie runs in |
| Gemini CLI | `~/.gemini/settings.json` | `mcpServers`; a remote server as `httpUrl` |

Antigravity and Cursor aren't supported yet.

## Secrets stay out of files

`env_from` names environment variables; brainrc writes a reference the tool expands when it
starts the server (`${NAME}`, `env_vars`, `{env:NAME}` or `${env:NAME}`), never the value; Junie, which reads
no reference, gets none. `validate` rejects a
server with an `env` table, which would hold values.

## Your own servers are safe

brainrc only replaces or removes servers it wrote itself (it keeps a list in
`~/.config/brainrc/mcp-owned.json`). If you already defined a server of the same name, `apply`
reports a `CONFLICT` and leaves yours alone. A backup of the file is written before every change.

## Pin their tools

An MCP server can change what its tools do after you approved it. `brainrc pin-mcp` guards
against that for Claude Code:

```bash
brainrc pin-mcp
```

It starts each stdio server brainrc installs, lists its tools, shows what changed since the last
pin, and on your yes records a hash of each tool's definition. At the start of each Claude Code
session a hook checks the tools again. If one changed, it warns you and tells the model not to call
it until you run `pin-mcp` again. HTTP servers aren't pinned, and the check gets 4 seconds for all servers
together: a server it can't reach in that time is skipped ([guardrails](guardrails.md#claude-code-hooks)).

`apply` names each stdio server whose tools aren't pinned yet.

The full format is in [formats](formats.md#mcp-servers-mcpserverstoml).
