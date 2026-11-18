# Concepts

The few words the rest of these docs use, in plain terms.

## Harness

An AI coding tool that reads config from your disk: Claude Code, Codex CLI, OpenCode, Antigravity
CLI and Cursor. Each keeps its skills, rules and settings in its own folder and format. brainrc
writes into the ones installed on your machine and skips the rest, unless `harnesses.local.toml`
turns one on or off ([configuration](configuration.md#harnesseslocaltoml)).
[What reaches each tool](capabilities.md) shows what each one gets.

## Item

One piece of config:

- a **rule**: text every session loads, such as "never push without asking";
- a **skill**: a folder of instructions a tool loads when the task calls for it;
- an **agent**: a role with its own prompt and tools, which another agent can hand work to;
- a **command**: a slash command;
- a **hook**: a script the tool runs at a set moment, such as the guard that asks before a
  `git push`;
- an **MCP server**: a tool the agent can call.

## Pack

A folder or git repo of items, one folder per kind (`rules/`, `skills/`, `agents/`, ...) and a
`pack.toml` that names it. brainrc itself ships only rules and guard hooks; everything else comes
from packs. You turn packs on in `packs.local.toml`, or a repo names them in its `brainrc.toml`
([packs](packs.md)).

The **default pack** is [Gatework](gatework.md), which takes a ticket to a pull request. It is on
unless you turn it off. Your own pack holds what you don't want in a public repo, such as your
employer's conventions.

## Profile

How much one machine installs from its packs: `minimal` (rules only), `recommended` (plus skills,
agents, commands and hooks) or `full` (plus MCP servers, the default). It lives in
`brainrc.local.toml`, with an `exclude` list to drop single items, and `brainrc init` asks for one
([configuration](configuration.md#brainrclocaltoml)).

## Lockfile

`brainrc.lock` records exactly what was installed: each git pack's commit and a SHA-256 hash of
each file. brainrc keeps a pack at its locked commit until you run `brainrc update`, so a moved tag
or branch never changes what you have. A repo commits its lock next to its `brainrc.toml`, and
every machine and CI job installs the same files (`brainrc install --frozen`), while
`brainrc check` fails when anything drifted ([team setup](project.md)).

## Scope

Where the files go. **User scope** writes into each tool's home folder (`~/.claude/`, ...): core,
the default pack and the packs in your `packs.local.toml`. **Project scope** writes into a repo
that has a `brainrc.toml` (`.agents/skills/`, `AGENTS.md`, ...), so everyone on the team gets the
same agent setup. `apply` does both: the user scope first, then the project you are in.

## Core

brainrc's own repo: the command, its rules (`rules/`), the guard hooks (`overrides/`) and the list
of where each tool reads its config (`harnesses.toml`). Packs declare which core versions they
work with (`requires_core`).

## status and apply

`brainrc status` shows what would change and writes nothing. `brainrc apply` makes the change: it
links items into each tool, renders rules into one file per tool, and merges hooks and MCP servers
into the tool's settings while keeping yours.
