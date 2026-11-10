# Example pack: homelab

A pack with one guard hook. It asks before commands that change Proxmox guests or Talos nodes,
which core's guard doesn't cover:

- `qm`/`pct` destroy, stop, shutdown, reboot, reset, rollback, migrate
- `talosctl` apply-config, upgrade, upgrade-k8s, reset, reboot, shutdown, bootstrap

Read-only commands (`qm list`, `talosctl dashboard`) pass. Host reboot and poweroff stay in core.
The hook is Claude Code only, and best effort: it matches the command text, so a quoted verb
(`qm "destroy" 1`), an option before the verb, a line continuation, or a command held in a
variable gets through.

## Enable it

In core's `packs.local.toml` (for an installed `brainrc`, `~/.config/brainrc/packs.local.toml`):

```toml
[homelab]
path = "~/brainrc/examples/pack-homelab"   # or a copy of this directory
```

```bash
python3 scripts/brainrc.py status
python3 scripts/brainrc.py apply
```

`apply` links `overrides/claude/hooks/` to `<hooks_dir>-homelab` and merges
`settings.fragment.json` after core's. To add your own rules, copy this directory and add to
`RULES` in `guard_homelab.py`, with a test for the risky command and a safe near-miss.
Format reference: [docs/packs.md](../../docs/packs.md#layout).
