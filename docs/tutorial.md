# Your first pack

In this tutorial you build a pack called `myteam` with one skill for Protocol Buffers, install it
into your AI tools, and check that Gatework will load it for `.proto` files. It takes about 15
minutes. You need Python 3.11+ and git.

A pack is a folder or repo of your own, layered on top of brainrc, so you never edit brainrc
itself ([packs](packs.md)). This tutorial works from a clone of brainrc so it can run the same
commands CI does; with the installed command, type `brainrc` where it says
`python3 scripts/brainrc.py`, and put `packs.local.toml` in `~/.config/brainrc/`.

Run every command from the brainrc clone unless a step says otherwise. CI runs steps 1-5 of this
page on every change (`scripts/check_tutorial.py`), so they stay accurate.

## 1. Clone brainrc, install it, and check it

```bash
git clone <this-repo> ~/brainrc
cd ~/brainrc
python3 scripts/brainrc.py apply
python3 scripts/brainrc.py validate
```

`apply` fetches the default pack, [Gatework](gatework.md), and installs brainrc and Gatework into
your AI tools. `validate` should then print a line starting with `OK:`
that counts skills, agents, and commands.

## 2. Create the pack

A pack needs a `pack.toml`. The `prefix` keeps your item names apart from everyone else's,
`requires_core` says which brainrc versions you tested against (see brainrc's `VERSION`), and the
`[[extensions.gatework.domains]]` row tells Gatework which files load your skill.

```bash
mkdir -p ~/src/myteam-ai-pack/skills/myteam-protobuf
cat > ~/src/myteam-ai-pack/pack.toml <<'EOF'
name = "myteam"
prefix = "myteam-"
requires_core = ">=0.6, <0.9"

[[extensions.gatework.domains]]
files = "`*.proto`, `buf.yaml`"
skills = ["myteam-protobuf"]
EOF
```

## 3. Write the domain skill

A domain skill, one for a single stack, has four sections: how to validate offline,
conventions, a review checklist, and what never to do without approval. The `description` is
what makes an AI tool load it.

```bash
cat > ~/src/myteam-ai-pack/skills/myteam-protobuf/SKILL.md <<'EOF'
---
name: myteam-protobuf
description: Protocol Buffers schemas for myteam services. Validation, conventions, and a review checklist for *.proto and buf.yaml. Use when changing or reviewing protobuf files.
---

# myteam-protobuf

## Validate (offline)
~~~bash
buf lint
buf breaking --against '.git#branch=main'
~~~

## Conventions
- One package per directory, named after the service and version (`myteam.billing.v1`).
- Never reuse or renumber a field. Reserve removed numbers and names.

## Review checklist
- A field changed type or number: that breaks every existing client.
- New required semantics on an existing message: needs a new version.

## Never without approval
- Publishing generated code or pushing to a schema registry.
EOF
```

## 4. Validate the pack

```bash
python3 scripts/brainrc.py validate --pack ~/src/myteam-ai-pack
```

You should see `OK:` with `(packs: gatework, myteam)` at the end: brainrc, the default pack it
fetched in step 1, and yours. A common mistake is a skill without
the prefix. `validate` then names it, for example
``myteam:skills/protobuf: pack skills must start with `myteam-` ``.

## 5. Enable and install it

Packs are enabled per machine in `packs.local.toml`, which git ignores. `status` is a dry run
and `apply` writes.

```bash
cat > packs.local.toml <<'EOF'
[myteam]
path = "~/src/myteam-ai-pack"
EOF
python3 scripts/brainrc.py status
python3 scripts/brainrc.py apply
python3 scripts/brainrc.py status | grep 'Everything in sync.'
```

The first `status` lists `CREATE` lines, including one for `myteam-protobuf` in each
harness's skills directory. After `apply`, `status` prints `Everything in sync.`

## 6. Check what your AI tools now see

```bash
ls ~/.claude/skills/myteam-protobuf
grep myteam ~/.config/brainrc/extensions.md
python3 scripts/brainrc.py tokens | grep myteam
```

You should see `SKILL.md`, a Domains row for `` `*.proto`, `buf.yaml` `` naming
`myteam-protobuf`, and the skill's cost in tokens. Gatework reads that Domains row at the
start of every ticket, so a ticket touching a `.proto` file now loads your skill.

## 7. Put the pack under version control

```bash
cd ~/src/myteam-ai-pack
git init -q
git add .
git -c user.name=you -c user.email=you@example.com commit -qm "Add myteam pack"
```

Then validate it in the pack's own CI on every push, against the brainrc version you pin
([Validate a pack in its own CI](packs.md#validate-a-pack-in-its-own-ci)):

```yaml
- uses: actions/checkout@<sha>
- uses: brainrc/brainrc/.github/actions/validate-pack@<brainrc tag>
```

## Next steps

- [examples/pack-acme](../examples/pack-acme/README.md) shows every other pack feature: an
  intake context skill, a ticket connector, Deliver checks, rules, commands, and tripwires.
- [Packs](packs.md) is the full pack reference.
- To share the pack with a repo's agents instead of one machine, list it in the repo's
  `brainrc.toml` ([team setup](project.md)).
- To add a domain skill to Gatework for everyone instead, open a pull request on
  [brainrc/gatework](https://github.com/brainrc/gatework): the skill goes in `skills/<stack>/`
  with a row in the Domains table of `skills/brainrc-gatework/SKILL.md`.
