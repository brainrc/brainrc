# {{name}}

{{description}}

A [brainrc](https://github.com/brainrc/brainrc) pack: brainrc installs its rules and skills into
every AI coding tool it manages, next to its own.

## Use it

On one machine, add it to brainrc's `packs.local.toml` and apply:

```toml
[{{name}}]
git = "<this repository's URL>"
ref = "<a tag>"
```

For every agent in one repository, add it to that repository's `brainrc.toml` instead, as
`[packs.{{name}}]` with the same keys.

## What's in it

| Path | What |
|---|---|
| `pack.toml` | the pack's name, its `{{prefix}}` prefix and the brainrc versions it works with |
| `rules/` | rules every session loads; keep them short |
| `skills/{{facts}}/` | facts about {{name}} that agents load when they need one |
| `tripwires.toml` | stale facts that must not come back |
| `tests/` | the pack's own tests |

## Change it

Read [AGENTS.md](AGENTS.md) first. Then check the pack the way its CI does:

```bash
brainrc validate --pack .
```
