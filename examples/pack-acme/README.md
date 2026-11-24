# Example pack: acme

A working pack to copy. It uses every pack feature except hooks: `requires_core`, a `[scope]`
(acme repos and ACME tickets), guard rules, a domain skill, an intake context skill, a ticket
connector config, a Deliver check, a reviewer agent, a rule, a command, and a tripwire. Format reference: [docs/packs.md](https://github.com/brainrc/brainrc/blob/main/docs/packs.md).

## Start your own

1. Copy this directory into a new repo: `cp -R examples/pack-acme ~/src/<name>-ai-pack`.
2. Rename `acme` everywhere: `name`, `prefix` and `id` in `pack.toml`, the skill, agent and command
   names (directories, files, and frontmatter `name`), and the text. Pick names that follow the
   [naming rules](https://github.com/brainrc/brainrc/blob/main/docs/packs.md#naming); set `id` to your GitHub handle and the repo name,
   or drop it.
3. Set `requires_core` to the core version you tested against (see `VERSION` in core).
4. Enable it on your machine in core's `packs.local.toml`, then check and apply:

   ```toml
   [<name>]
   path = "~/src/<name>-ai-pack"
   ```

   ```bash
   python3 scripts/brainrc.py status
   python3 scripts/brainrc.py apply
   ```

5. Validate it in the pack's own CI with core's `validate-pack` action, pinned to the core
   version you tested against. It fetches Gatework, the pack this one extends, too:

   ```yaml
   # .github/workflows/validate.yml
   on: [push, pull_request]
   jobs:
     validate:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@<sha>
         - uses: brainrc/brainrc/.github/actions/validate-pack@<core tag>
   ```

   Core's own CI checks this example with the same action. A pre-commit hook and the manual
   step are in [docs/packs.md](https://github.com/brainrc/brainrc/blob/main/docs/packs/validate-in-ci.md).

Hooks are left out on purpose: an enabled pack's hooks run on every tool call. Its guard rules
(`[[guard.deny]]`, `[[guard.ask]]`) need none: core's guard enforces them, only inside acme repos
or on an ACME ticket. To add hooks anyway,
see `overrides/` in [docs/packs.md](https://github.com/brainrc/brainrc/blob/main/docs/packs.md#layout) and the
[homelab example](https://github.com/brainrc/brainrc/blob/main/examples/pack-homelab/README.md).
