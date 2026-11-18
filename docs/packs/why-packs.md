<!-- divio: explanation -->
# Why packs, and what you trust when you turn one on

A pack is the unit brainrc shares instructions in. This page explains why it's a separate unit
from brainrc itself, and what keeps a pack you didn't write from doing more than you agreed to.

## Why a pack, not a fork

brainrc's own rules and hooks are generic: they say how an agent should work anywhere. What an
agent needs to know about one employer, team or stack (its hosts, ticket keys, review rules,
domain skills) changes on another schedule and often can't be public. Keeping that in a pack
means brainrc can be updated without merging into your copy, and a pack can be private, versioned
and owned by the people who know its subject.

One pack also reaches every tool. A pack's skills, agents, commands, rules, hooks and MCP servers
are written once, and `apply` renders them into each harness's own format and place. The same
pack listed in a repository's `brainrc.toml` gives every agent that opens the repository the same
files, through `AGENTS.md` and `.agents/skills/`, whether or not each person runs brainrc.

## Rules cost every session; skills cost one

A rule is loaded into every session on every machine with the pack, so it is paid for whether or
not the task needs it. A skill's description is loaded, and its body only when a task calls for
it. That is why `new pack` writes one short rule that points at a facts skill, and why
`max_always_tokens` and `brainrc tokens` exist: the budget is shared with every other pack and
with the work itself ([context cost](../packs.md#context-cost)).

## The trust model

Turning a pack on runs its hooks, starts its MCP servers and puts its text in front of your
agents. brainrc can't judge whether that text is good advice, so it makes sure you can see what a
pack can do, that it can't change unseen, and that its code runs only where you chose.

- **Names say who it's from.** `brainrc-` and `brainrc/` belong to official packs, a published
  pack's prefix starts with its owner's handle, and names one or two edits from an official name
  or using a vendor's are refused. Every item starts with its pack's prefix, so one pack can't
  replace another's skill ([naming](../packs.md#naming)).
- **What it can do is in the lock.** `brainrc.lock` records each pack's hooks, MCP servers, tool
  grants and the hosts they reach. `apply` shows a `PERMS` line for each new one and asks before
  writing; in CI, with no one to ask, it refuses. `install --frozen` installs only what the lock
  holds ([permissions](../project.md#permissions)).
- **What it is can't move.** The lock pins each git pack to a commit and every file to a hash.
  `brainrc check` fails when a file differs, with no network; `update` is the one command that
  moves a pack, and it shows what changed first ([pinned commits](../project.md#pinned-commits-and-update)).
- **Its code runs only where you chose.** A pack's validator runs inside brainrc only for a
  default pack, for `validate --pack`, or when you set `run_validator = true` for it. Its tests
  run only from `validate --pack` on the command line, never from `apply` or `doctor`
  ([validator plugins](../packs.md#validator-plugins), [pack tests](../packs.md#pack-tests)).
- **It says which brainrc it fits.** `requires_core` stops `apply` writing anything when brainrc
  is outside the range the pack was tested with ([compatibility](../packs.md#compatibility)).
- **Old mistakes stay fixed.** A pack's tripwires fail `validate` when a retired tool, host or
  path comes back in any file ([tripwires](../packs.md#tripwirestoml)).

None of this reviews a pack's instructions for you. Read a pack's rules and hooks before you turn
it on, the way you'd read a dependency's install script, and pin it to a tag or commit.

## Packs and Claude Code plugins

brainrc also ships as a Claude Code plugin ([plugins](../plugins.md)), but packs need the
`brainrc` command: a plugin could carry a pack's skills, agents and hooks, but not its rules or
its Gatework extensions (domains, ticket connector, Deliver checks), which `brainrc apply`
renders, and it reaches only Claude Code. This may change if plugins gain a way to extend another
plugin. To move a plugin of your own into a pack, see [from a plugin](from-a-plugin.md).
