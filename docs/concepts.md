# Concepts

The few words the rest of these docs use, in plain terms.

## Harness

An AI coding tool that reads config from your disk: Claude Code, Codex CLI, OpenCode, Antigravity
CLI and Cursor. Each keeps its skills, rules and settings in its own folder and format.
`brainrc` writes into the ones installed on your machine and skips the rest, unless
`harnesses.local.toml` turns one on or off ([install](install.md#per-machine-customization-never-committed)).
[Harness support](formats.md#harness-support) shows what reaches each one.

## Item

One piece of config: a **skill** (a folder of instructions a tool loads when the task calls for
it), an **agent** (a role with its own prompt and tools), a **command** (a slash command), a
**rule** (text every session loads), a **hook** (a script the tool runs at a set moment, such as
the guard that asks before a `git push`, or the check at session start) or an **MCP server** (a
tool the agent can call).

## Pack

A folder or git repo of items, one folder per kind (`skills/`, `agents/`, `rules/`, ...;
[packs](packs.md#layout) has the layout). You turn packs on in `packs.local.toml`, or a repo names them in its
`brainrc.toml`. `brainrc` itself ships only rules and guard hooks; everything else comes from
packs. Its default pack is [Gatework](https://github.com/brainrc/gatework), which carries
spec-agent and the domain skills, and you can turn it off. Your own pack holds what must stay
private, such as an employer's facts ([packs.md](packs.md)).

## Profile

What one machine installs from the packs it has: from rules only up to everything, MCP servers
included. It lives in `brainrc.local.toml`, with an `exclude` list to drop single items, and
`brainrc init` asks for one. The profiles and what each installs are in
[install](install.md#per-machine-customization-never-committed).

## Lockfile

`brainrc.lock` records exactly what was installed: each pack's commit and a SHA-256 hash of each
file. Commit it with a repo's `brainrc.toml`, and every machine and CI job installs the same
files (`brainrc install --frozen`), while `brainrc check` fails when anything drifted. Your
machine keeps its own lock too ([project.md](project.md)).

## Scope

Where the files go. **User scope** writes into each harness's home folder (`~/.claude/`, ...):
core, the default pack and the packs in your `packs.local.toml`. **Project scope** writes into a repo that has a `brainrc.toml`, so a team
shares the same agent setup.

## status and apply

`brainrc status` shows what would change and writes nothing. `brainrc apply` makes the change:
it links items into each harness, renders rules, and merges hooks and MCP servers into the
tool's settings while keeping yours.
