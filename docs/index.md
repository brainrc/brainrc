# brainrc

brainrc installs one set of AI coding-agent config into Claude Code, Codex CLI, OpenCode,
Antigravity CLI and Cursor: skills, rules, agents, commands, guard hooks and MCP servers, from
packs you choose.

```bash
uvx brainrc status          # preview; writes nothing
uv tool install brainrc     # or: pipx install brainrc
brainrc apply
```

- **New here:** [install](install.md), then the [tutorial](tutorial.md).
- **Your own content:** [packs](packs.md), and a repo's shared, pinned setup in
  [the project manifest and lockfile](project.md).
- **What reaches each tool:** [harness support](formats.md#harness-support).
- **What the guard hooks catch:** [guardrails](guardrails.md).
- **File formats:** [formats](formats.md) and the [JSON Schemas](schemas.md).

The source is [github.com/brainrc/brainrc](https://github.com/brainrc/brainrc). Each release has
its own version of this site; the version menu at the top switches between them.
