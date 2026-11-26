<!-- divio: how-to -->
# Publish a pack for a stack

Share what agents should know about one language, framework or platform, for anyone to turn on.

## 1. Pick a name you can publish

Publish the pack under your GitHub handle, with a prefix that starts with it. Names that look
like an official pack's or use a vendor's name are refused ([naming](../packs.md#naming)):

```bash
brainrc new pack jdoe-elixir --id jdoe/elixir --prefix jdoe-elixir-
```

## 2. Write one domain skill per stack

A domain skill has four sections: how to validate offline, conventions, a review checklist, and
what never to do without approval. Its `description` says when to load it. The
[tutorial](../tutorial.md#3-add-a-domain-skill) writes one in full.

## 3. Tell Gatework which files load it

```toml
[[extensions.gatework.domains]]
files = "`*.ex`, `*.exs`, `mix.exs`"
skills = ["jdoe-elixir-phoenix"]
reviewer = "brainrc-code-reviewer"   # optional: the agent that reviews these files
```

## 4. Say which brainrc versions it works with

`new pack` pins `requires_core` to the minor series you ran it with, and its CI workflow and
pre-commit hook to that release's tag. When you test against a newer brainrc, move all three
together ([compatibility](../packs.md#compatibility)).

## 5. Release it

Tag a release, and tell people to pin the tag:

```toml
[jdoe-elixir]
git = "https://github.com/jdoe/elixir-pack.git"
ref = "v1.0.0"
```

A domain skill everyone should get can go into an official pack instead: open a pull request on
[brainrc/packs](https://github.com/brainrc/packs) that adds the skill to its stack's folder (or a
new folder for a new stack) with an `[[extensions.gatework.domains]]` row in that folder's
`pack.toml`.
