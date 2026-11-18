<!-- divio: how-to -->
# Start a pack for your employer

Keep what only your employer's agents should know (internal hosts, ticket keys, review rules) out
of brainrc and out of public repositories, in a private pack every colleague turns on.

## 1. Write it into a private repository

```bash
brainrc new pack acme --to ~/src/acme-ai-pack --ticket jira --host acme.atlassian.net --refs 'ACME-*'
```

`--ticket jira` adds an `[extensions.gatework.ticket]` table, so Gatework uses its Jira connector
for `ACME-*` refs. Use `--ticket github` for GitHub issues, or leave it out. Push the folder to a
private repository; its CI workflow checks it on every push ([validate in CI](validate-in-ci.md)).

## 2. Fill in the facts, not the rules

Put hosts, repositories, tools and teams in `skills/acme-facts/SKILL.md`. It loads only when a
task needs it. Keep `rules/` for the few things every session must follow, written as a narrower
case of brainrc's rules ("in Acme repos, also ..."): rules load into every session on every
machine with the pack ([rules](../packs.md#rules), [context cost](../packs.md#context-cost)).

## 3. Add what your team checks before a PR

Add a line to `deliver_checks` for each check Gatework should list at its Deliver gate, and a
`[[extensions.gatework.domains]]` row for each file pattern that should load one of your skills
([extensions](../packs.md#extensions)):

```toml
[extensions.gatework]
deliver_checks = ["Deploy plan reviewed by the owning team"]
```

## 4. Stop stale facts coming back

When a tool is retired or a host renamed, change the facts skill and add a tripwire for the old
name, so `validate` fails if anyone writes it again ([tripwires](../packs.md#tripwirestoml)):

```toml
[[tripwire]]
id = "retired-deploy-tool"
pattern = '(?i)\bshipit\b'
message = "shipit was retired. Deploys go through the acme-deploy skill."
allow = '(?i)retired|never'
```

## 5. Turn it on

Each colleague adds it by git URL, pinned to a tag, and applies; git uses their own credentials
for the private repository ([use a pack](use-a-pack.md)):

```toml
[acme]
git = "git@github.com:acme/acme-ai-pack.git"
ref = "v1.0.0"
```

To give every agent in one of the employer's repositories the pack, list it in that repository's
`brainrc.toml` instead ([team pack](team-pack.md)).
