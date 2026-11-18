# mypack

A template for a [brainrc](https://github.com/brainrc/brainrc) pack. Use it from GitHub
(**Use this template**), then make it yours before you add anything:

1. Pick a name and a prefix that follow brainrc's
   [naming rules](https://github.com/brainrc/brainrc/blob/main/docs/packs.md#naming), for example
   `acme` and `acme-`.
2. In `pack.toml`, set `name`, `prefix` and `description`.
3. Rename `rules/10-mypack.md` and `skills/mypack-facts/`, and change `mypack` in that skill's
   `name:` and in the rule.
4. Replace this section, and `mypack` below, with your pack's name.
5. Run `grep -rn mypack .` to find what's left, then `brainrc validate --pack .`.

Or skip the template: `brainrc new pack acme` writes the same files with your name in them.

Rules and facts for mypack's AI coding agents.

A [brainrc](https://github.com/brainrc/brainrc) pack: brainrc installs its rules and skills into
every AI coding tool it manages, next to its own.

## Use it

On one machine, add it to brainrc's `packs.local.toml` and apply:

```toml
[mypack]
git = "<this repository's URL>"
ref = "<a tag>"
```

For every agent in one repository, add it to that repository's `brainrc.toml` instead, as
`[packs.mypack]` with the same keys.

## What's in it

| Path | What |
|---|---|
| `pack.toml` | the pack's name, its `mypack-` prefix and the brainrc versions it works with |
| `rules/` | rules every session loads; keep them short |
| `skills/mypack-facts/` | facts about mypack that agents load when they need one |
| `tripwires.toml` | stale facts that must not come back |
| `tests/` | the pack's own tests |

## Change it

Read [AGENTS.md](AGENTS.md) first. Then check the pack the way its CI does:

```bash
brainrc validate --pack .
```
