# JSON Schemas

Each brainrc config file has a JSON Schema that describes it after it is parsed as TOML.
`brainrc` checks the files against them, and an editor that reads `#:schema` lines (Taplo,
Even Better TOML) completes and checks them as you type ([packs](packs.md#editor-completion)).

| File | Schema | What it is |
| --- | --- | --- |
| `pack.toml` | [pack.toml.schema.json](schemas/pack.toml.schema.json) | a pack's manifest ([packs](packs.md#packtoml)) |
| `mcp/servers.toml` | [mcp-servers.toml.schema.json](schemas/mcp-servers.toml.schema.json) | a source's MCP servers ([formats](formats.md)) |
| `harnesses.toml` | [harnesses.toml.schema.json](schemas/harnesses.toml.schema.json) | where each tool reads its config ([formats](formats.md#harness-support)) |
| `brainrc.toml` | [brainrc.toml.schema.json](schemas/brainrc.toml.schema.json) | a repo's project manifest ([project](project.md)) |
| `brainrc.lock` | [brainrc.lock.schema.json](schemas/brainrc.lock.schema.json) | the user or project lock ([project](project.md)) |

`schemas/pack-api/` holds the frozen contract of each pack API version, which packs pin with
`requires_api` ([compatibility](packs.md#compatibility)).

To point an editor at the copy for `main`, put this line at the top of the file:

```toml
#:schema https://raw.githubusercontent.com/brainrc/brainrc/main/docs/schemas/pack.toml.schema.json
```
