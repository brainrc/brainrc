---
bump: patch
---
- The CLI is built on argparse: `brainrc --help` and `--version` exit 0, every command has its own `--help`, and the maintainer commands `plugin` and `release` no longer show in the command list (they still run). A usage error goes to stderr with exit 2. `status` and `apply` take `--only <harness>` (repeatable, or comma-separated) to touch only those harnesses; the others keep their links, hooks and MCP servers as they are.
