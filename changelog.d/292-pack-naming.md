---
bump: minor
---
- **[pack contract]** Pack naming rules, in [docs/packs.md](docs/packs.md#naming): `brainrc-` and `brainrc/` are reserved for official packs, a registry prefix starts with the owner's handle, no vendor names without verification, no names one or two edits from an official name, ASCII lowercase letters, digits and hyphens only, a prefix is 2 to 24 characters, and item names are prefix-scoped. The page lists the official pack IDs (#293).
- **[pack contract]** `validate` and `apply` enforce the rules, and `pack.toml` takes an optional `id = "<owner>/<pack>"`, the ID a pack is published under. A pack that broke a rule now fails; rename it, or its prefix, to fix it (#294).
- Core agents are now `brainrc-analyst`, `brainrc-architect`, `brainrc-code-reviewer`, `brainrc-doc-writer`, `brainrc-implementer`, `brainrc-infra-reviewer`, `brainrc-researcher`, `brainrc-security-reviewer`, `brainrc-test-writer` and `brainrc-verifier`, and spec-agent dispatches those names. The old names stay as deprecated aliases with the same tools and model until 0.7.0, so a pack's `reviewer = "infra-reviewer"` keeps working; switch it to the `brainrc-` name. `validate` checks the aliases and rejects a new core agent without the prefix (#295).
- The example packs pin `requires_core = ">=0.5, <0.7"`.
