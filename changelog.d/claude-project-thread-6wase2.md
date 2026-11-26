---
bump: patch
---
- Gatework's pin moves to v0.9.0. Gatework 0.9 no longer ships `brainrc-go-service`,
  `brainrc-db-migrations`, `brainrc-terraform`, `brainrc-aws`, `brainrc-kubernetes`,
  `brainrc-gitops` or `brainrc-containers`: enable the official `brainrc/go`,
  `brainrc/terraform-aws` and `brainrc/kubernetes` packs from brainrc/packs to keep them
  (docs/upgrade.md). The `app` starter no longer excludes them, and switching starters clears the
  old exclude lines.
- The docs pin brainrc/packs at its first tag, `v0.1.0`, instead of `v1.0.0`.
