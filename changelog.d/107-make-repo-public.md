---
bump: patch
---
- Core's guard no longer asks about Proxmox `qm`/`pct` or `talosctl`: those rules moved to
  `examples/pack-homelab`, the first example pack with a guard hook. Enable it to keep the
  prompts (#107).
- Run records keep no home-directory paths: `state.json` writes `worktree` with `~` (#107).
