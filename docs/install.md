# Install and sync (brainrc)

brainrc is one Git repo of AI coding-assistant configuration (skills, agents, slash
commands, rules, hooks, and MCP servers), written once and synced into Claude Code, Codex CLI,
OpenCode, Antigravity CLI, and Cursor by `brainrc`. Skills reach every harness. Rules, commands,
and agents reach only some so far. Guard hooks run in Claude Code, OpenCode, and Cursor (deny
only in the last two), and MCP servers sync to Claude Code, Codex, and OpenCode.
Details per harness: [harness support](formats.md#harness-support).

## Install with a clone

```bash
git clone <this-repo> ~/brainrc
cd ~/brainrc
python3 scripts/brainrc.py status   # dry run: shows what would be linked
python3 scripts/brainrc.py apply    # render rules + create symlinks
```

Skills, agents, commands, and hooks are **symlinked** from each harness back into this repo,
so `git pull` updates them in every harness at once. To stay on a release instead of `main`,
check out its tag (`git checkout v0.3.29`) and re-run `apply`. Rules are different: they are rendered
into `~/.config/brainrc/instructions.md` (`$BRAINRC_HOME` to change it; `$XDG_CONFIG_HOME/brainrc` when that is set), so re-run `apply` after any change to `rules/` (edits included),
and after you add or remove skills, agents, or commands. For Claude Code, `apply` also merges
the guard hooks into `~/.claude/settings.json` (your other hooks are kept; a backup is written
first, and the last 5 backups are kept).

## Install without a clone

`brainrc` also installs as a command, with core's skills, agents, rules, and hooks bundled:

```bash
uv tool install git+https://github.com/brainrc/brainrc   # or: pipx install git+https://github.com/brainrc/brainrc
brainrc status
brainrc apply
```

Pin a release with `git+https://github.com/brainrc/brainrc@v<X.Y.Z>` (0.4.0 or later installs as `brainrc`).

Already have the old `ai-config` package installed? Run `uv tool uninstall ai-config`
(or `pipx uninstall ai-config`): its `aicfg` command is outdated and works on the old settings home.
The `aicfg` command was removed in 0.5.0: use `brainrc`.

Links then point into the installed package, so `uv tool upgrade brainrc` (or `pipx upgrade
brainrc`) updates every harness. Guard hooks are the exception: `apply` copies them to
`$BRAINRC_HOME/hooks/core/` and links there, because the package path changes when an upgrade
moves the tool to a new Python. Run `brainrc apply` after upgrading to refresh the copy. After an
upgrade to a new Python, the other links (skills, agents) point at the old path and `apply`
reports them as `CONFLICT`; `brainrc doctor` lists each broken link with the `rm` that clears it,
then re-run `apply`. Local files go in `~/.config/brainrc/` (`$BRAINRC_HOME`):
`harnesses.local.toml`, `packs.local.toml`, and `rules/*.local.md`. Packs are local
directories or git URLs that `brainrc` fetches ([packs](packs.md#enable-a-pack)).

Upgrading from the legacy `~/.config/ai-config/` (or `$AICFG_HOME`)? 0.5.0 no longer reads them, and
`status`, `apply` and `update` refuse (writing nothing) until you migrate. Run `brainrc migrate --dry-run` to see
the move, then `brainrc migrate`: it moves the directory and re-runs `apply`. With the old `AICFG_HOME` set, set
`BRAINRC_HOME` to the new location first.

`plugin` needs a checkout. Contributors use the clone above.

`brainrc` never overwrites a file it doesn't manage. Pre-existing files show up as
`CONFLICT` for you to move into the repo or delete.

Something missing in a harness? `python3 scripts/brainrc.py doctor` checks the install without
changing anything: stale rules, missing or broken links (after moving the repo, say), broken
packs, unmerged hooks, and harnesses that aren't installed. Each problem comes with its fix.
[troubleshooting.md](troubleshooting.md) covers the rest, including how to uninstall.

## Plugins (no clone)

### Claude Code

Claude Code users can install the skills (including `/work`), agents, and guard hooks as a plugin:

```text
/plugin marketplace add brainrc/brainrc
/plugin install brainrc@brainrc
```

| Piece | Plugin | `brainrc` |
|---|---|---|
| Skills, agents | yes, named `brainrc:<name>` (`/brainrc:work`) | yes |
| Claude guard hooks | yes | yes |
| Rules (`rules/`) | no: plugins can't load instructions into every session | yes |
| Packs, other harnesses (Codex, OpenCode, Antigravity, Cursor) | no | yes |

Use one path, not both: together they load every skill and hook twice. For rules with the
plugin, copy `rules/*.md` into your own `~/.claude/CLAUDE.md`.

### Codex

```text
codex plugin marketplace add brainrc/brainrc
codex plugin add brainrc@brainrc
```

Codex gets the skills (`work`, `review`, `spec-*`, and the rest) and the agent files spec-agent
reads. Rules don't come with a Codex plugin: run `brainrc`, or copy `rules/*.md` into
`~/.codex/AGENTS.md`. Whether Codex runs the plugin's guard hooks is not yet verified
([harness packages](harness-packages.md#codex)).

### Antigravity CLI

Antigravity CLI (`agy`) installs the repo as a plugin from the root `plugin.json`:

```text
agy plugin install https://github.com/brainrc/brainrc
```

It gets the skills, the agent files, and the rules: each `rules/*.md` carries
`trigger: always_on`, which Antigravity needs to load it. Guard hooks aren't included yet, so use
agy's own permission settings. This install was built from Antigravity's public docs and issues
and hasn't been run end to end
([harness packages](harness-packages.md#antigravity-cli)).

### Cursor

Cursor loads a checkout as a local plugin from `.cursor-plugin/`:

```bash
ln -s ~/src/brainrc ~/.cursor/plugins/local/brainrc
```

It gets the skills, the agents, the rules (each carries `alwaysApply: true`), and the guard
hooks for shell commands and file reads, which deny instead of asking. Use the plugin or
`brainrc`'s Cursor links, not both: `brainrc` links the same skills and hooks (Cursor has no user
rules file, so rules come only with the plugin). Built from Cursor's official plugin repo and not
yet run in a real Cursor ([harness packages](harness-packages.md#cursor)).

### Moving from ai-config

The plugin was renamed from the old `ai-config` to `brainrc`, and its skills from the old `ai-config:<name>` to
`brainrc:<name>`. Remove the old one first, or every skill and hook loads twice:

- Claude Code: `/plugin uninstall ai-config@ai-config`, then `/plugin marketplace remove ai-config`.
- Codex: uninstall `ai-config@ai-config` and remove its marketplace, per Codex's docs.
- Cursor: delete the old link `~/.cursor/plugins/local/ai-config`.

Then install `brainrc@brainrc` as above. `doctor` warns until the old plugin is gone.

## Platforms

macOS and Linux. Everything installs by symlink, and spec-agent reads its role files through
the `skills/spec-agent/roles` symlink, so the checkout needs symlinks too. On Windows, use WSL,
or turn on Developer Mode and run `git config --global core.symlinks true` before cloning.
`validate` and `doctor` report a checkout without symlinks, with the fix.

## Per-machine customization (never committed)

| File | Purpose |
|---|---|
| `harnesses.local.toml` | Disable a harness or change paths (`[cursor]` / `enabled = false`) |
| `packs.local.toml` | Layer extra repos on top: skills, agents, rules, hooks, spec-agent extensions ([packs.md](packs.md)) |
| `rules/*.local.md` | Private rules appended after the shared ones |

Content that must never live in this repo (an employer's facts and skills, for example) goes
in a **pack**: a separate repo with the same layout. See [packs.md](packs.md).
`python3 scripts/brainrc.py tokens` shows what each skill, agent, and rule costs in context.

## Layout

```
rules/          Global instructions, as ordered markdown fragments (00-core.md, 10-git.md, ...).
                Concatenated into CLAUDE.md / AGENTS.md.
skills/<name>/  Agent Skills: spec-agent engine, ticket connectors, domain skills (terraform, aws, ...).
agents/         Agent roles (analyst, architect, implementer, reviewers, verifier, doc-writer).
commands/       Optional, for packs: slash commands. Core's (/work, /review, /spec-*) are skills.
mcp/            Canonical MCP server registry. Env var names only, never secret values.
overrides/      Harness-specific config (Claude guard hooks + settings fragment).
harnesses.toml  Where each harness reads each content type.
packs.toml      Extra source repos ("packs") layered on top; usually set in packs.local.toml.
VERSION         Core version that packs pin with `requires_core`; changes in CHANGELOG.md.
changelog.d/    One fragment per unreleased change; folded into CHANGELOG.md on release.
brainrc/        The brainrc package: sync, validate, doctor, plugin, tokens (Python 3.11+, stdlib only).
scripts/        brainrc.py (runs the package), evals.py, release.py.
docs/           spec-agent, guardrails, efficiency, formats, troubleshooting, harness packages, roadmap.
tests/          stdlib unittest for brainrc and hooks.
examples/       Sandbox project + tickets for trying spec-agent.
dist/           Generated output (gitignored).
```
