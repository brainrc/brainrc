<!-- divio: how-to -->
# Use a pack

Turn a pack on for this machine, move it to a newer version, or turn the default pack off. For a
pack every agent in one repository gets, see [team setup](../project.md).

## Enable a pack

List it in `packs.local.toml` ([where that file lives](../configuration.md#where-the-files-live)),
then apply:

```toml
[acme]
path = "~/src/acme-ai-pack"   # ~ and $VARS expand; relative paths are relative to this file
# enabled = false             # removes the pack's links and hooks on the next apply
```

```bash
brainrc status   # preview
brainrc apply
```

Or name it by git URL and let brainrc fetch it, with no clone of your own:

```toml
[acme]
git = "git@github.com:acme/acme-ai-pack.git"   # any URL git accepts; private repos use your git credentials
ref = "v1.2.0"                                 # tag, branch, or commit; default: the remote's default branch
```

`apply` fetches it into `~/.config/brainrc/packs/acme`; after that it works offline. It records
the commit the ref resolved to, and a hash of every file it installed, in
`~/.config/brainrc/brainrc.lock`, and from then on **keeps the pack at that commit**, even when the
tag or branch moves. To move it:

- `brainrc update [<pack> ...]` refetches at the `ref`, prints the commits and files that change,
  then applies ([pinned commits](../project.md#pinned-commits-and-update)).
- Changing `ref` or `git` fetches the new one on the next `apply` (`status` shows a `FETCH` line).

Both refuse a clone with local changes, and stop any git call after 60 seconds. Pin a tag, and
bump `ref` to upgrade. `doctor` reports a git pack that isn't fetched yet or doesn't match its
`git` and `ref`.

The lock also records what each pack can do: its hooks, MCP servers, tool grants and network
domains. `status` lists any added (`PERMS ... +`) or removed, and `apply` asks before adding any
unless you pass `--yes` ([permissions](../project.md#permissions)).

## Turn the default pack off or pin it

A default pack is on unless you turn it off. [Gatework](../gatework.md) is the only one: its engine
(the `brainrc-gatework` skill), its roles, the ticket connectors and the domain skills. It lives in
[brainrc/gatework](https://github.com/brainrc/gatework), and brainrc's own `packs.toml` pins it to a
release tag, so `apply` fetches it like any git pack.

In `packs.local.toml`:

```toml
[gatework]
enabled = false        # turn it off: brainrc then installs only its rules and guard hooks
```

```toml
[gatework]
ref = "v<X.Y.Z>"       # pin another Gatework release; its git URL is kept
```

```toml
[gatework]
path = "~/src/gatework"   # work on a clone; replaces the shipped git and ref
```

`brainrc init` asks whether to keep it. Gatework 0.8.0 stopped installing its old names
(`spec-agent`, `spec-status`, `kubernetes` and the rest); the next `apply` removes their links
([old names](../upgrade.md#from-spec-agent)).

`validate --pack` checks a pack against brainrc and the default packs on disk, so a pack that
extends Gatework is checked against it once `apply` has fetched it; until then `validate` warns.
`--fetch-defaults` fetches them at the versions brainrc pins instead
([CI](validate-in-ci.md)).
