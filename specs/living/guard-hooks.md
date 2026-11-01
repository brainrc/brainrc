# guard-hooks

What the core and example-pack guard hooks ask about before a command runs.

### Homelab guards in an example pack
Core's outward guard SHALL NOT ask about Proxmox `qm`/`pct` or `talosctl` commands. The
`examples/pack-homelab` hook SHALL ask about `qm`/`pct` destroy/stop/shutdown/reboot/reset/
rollback/migrate and `talosctl` apply-config/upgrade/upgrade-k8s/reset/reboot/shutdown/bootstrap,
and stay silent for read-only commands. (AC1, AC2, AC3)
_Last changed by 107-make-repo-public._
