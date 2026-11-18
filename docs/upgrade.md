# Upgrading

Two things move independently: the `brainrc` command, and the packs it installs.

## Upgrade brainrc

```bash
uv tool upgrade brainrc          # or: pipx upgrade brainrc, brew upgrade brainrc
brainrc apply --repair
```

Run `apply` after every upgrade. It refreshes the copy of the guard hooks your tools run, and
`--repair` relinks skills and agents whose links still point at the old version (an upgrade can
move the package to a new Python, and Homebrew keeps each version in its own folder).

From a clone, `git pull` (or `git checkout v<X.Y.Z>` for a release), then
`python3 scripts/brainrc.py apply`.

What changed in each release is in the [CHANGELOG](../CHANGELOG.md). Changes that affect packs are
tagged **[pack contract]**.

## Move packs to newer versions

`apply` keeps each git pack at the commit recorded in `brainrc.lock`, even when its tag or branch
moves. To take what the pack's `ref` points at now:

```bash
brainrc update              # every git pack
brainrc update gatework     # or just one
```

`update` prints the commits and files that change, then applies and relocks. To move to another
tag, change `ref` in `packs.local.toml` (or the repo's `brainrc.toml`) and run `apply`.

A new brainrc release can also pin a newer Gatework in its own `packs.toml`; the next `apply`
fetches it.

## From ai-config

brainrc's old name, before 0.4.0, was `ai-config`, with an `aicfg` command and settings in
the old `~/.config/ai-config`. If you used the old name:

1. Remove the old package: `uv tool uninstall ai-config` (or `pipx uninstall ai-config`).
   The `aicfg` command was removed in 0.5.0: use `brainrc`.
2. Move the old settings home: `brainrc migrate --dry-run` shows the move, `brainrc migrate`
   does it and runs `apply`. With the old `AICFG_HOME` set, set `BRAINRC_HOME` to the new place
   first. Until you migrate, `init`, `status`, `apply`, `update`, `install`, `uninstall` and
   `pin-mcp` refuse and write nothing.
3. Replace the old plugin, as below.

### Moving from ai-config

The plugin was renamed from the old `ai-config` to `brainrc`, and its skills from the old
`ai-config:<name>` to `brainrc:<name>`. Remove the old one first, or every skill and hook loads
twice:

- Claude Code: `/plugin uninstall ai-config@ai-config`, then `/plugin marketplace remove ai-config`.
- Codex: uninstall `ai-config@ai-config` and remove its marketplace, per Codex's docs.
- Cursor: delete the old link `~/.cursor/plugins/local/ai-config`.

Then install `brainrc@brainrc` ([plugins](plugins.md)). `doctor` warns until the old plugin is
gone.

## From spec-agent

Gatework's engine was called spec-agent before brainrc 0.7. Its skills and agents now start with
`brainrc-`:

| Old name | New name |
|---|---|
| `spec-agent` | `brainrc-gatework` |
| `/spec-status`, `/spec-approve`, `/spec-resume` | `/brainrc-gatework-status`, `/brainrc-gatework-approve`, `/brainrc-gatework-resume` |
| `ticket-github`, `ticket-jira`, `ticket-local` | `brainrc-ticket-github`, `brainrc-ticket-jira`, `brainrc-ticket-local` |
| `kubernetes`, `unslop` and the other domain skills | `brainrc-kubernetes`, `brainrc-unslop`, ... |
| `analyst`, `verifier` and the other agents | `brainrc-analyst`, `brainrc-verifier`, ... |
| `[extensions]`, `[extensions.spec-agent]` in `pack.toml` | `[extensions.gatework]` |

Gatework 0.8.0 no longer installs the old names in this table: the next `brainrc apply` removes
their links. A pack that still names one in `[extensions.gatework]` works with a warning until
Gatework 0.9.0. Use the new names. The older `/work`, `/review`, `/plan`, `aws` and `terraform`
were removed in 0.6.0: use `/brainrc-work`, `/brainrc-review`, `/brainrc-plan`, `brainrc-aws`
and `brainrc-terraform`.
