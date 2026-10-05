# Example pack: acme

A working pack to copy. It uses every pack feature except hooks: `requires_core`, a domain
skill, an intake context skill, a ticket connector config, a Deliver check, a rule, a command,
and a tripwire. Format reference: [docs/packs.md](../../docs/packs.md).

## Start your own

1. Copy this directory into a new repo: `cp -R examples/pack-acme ~/src/<name>-ai-pack`.
2. Rename `acme` everywhere: `name` and `prefix` in `pack.toml`, the skill and command names
   (directories, files, and frontmatter `name`), and the text.
3. Set `requires_core` to the core version you tested against (see `VERSION` in core).
4. Enable it on your machine in core's `packs.local.toml`, then check and apply:

   ```toml
   [<name>]
   path = "~/src/<name>-ai-pack"
   ```

   ```bash
   python3 scripts/aicfg.py status
   python3 scripts/aicfg.py apply
   ```

5. Validate it in the pack's own CI:

   ```bash
   git clone <core-repo> core
   python3 core/scripts/aicfg.py validate --pack .
   ```

Hooks are left out on purpose: an enabled pack's hooks run on every tool call. To add them,
see `overrides/` in [docs/packs.md](../../docs/packs.md#layout).
