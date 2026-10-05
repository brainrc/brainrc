# Changelog

The core version lives in [`VERSION`](VERSION). Packs pin it with `requires_core`
([docs/packs.md](docs/packs.md#compatibility)).

Entries tagged **[pack contract]** change what packs can rely on: `pack.toml` keys and
extensions, the rendered `extensions.md`, naming and layout rules. While the version is `0.x`,
a breaking pack-contract change bumps MINOR. After `1.0`, it bumps MAJOR.

## 0.1.0 (2026-10-05)

First versioned release. All entries but the first shipped before versioning began.

- **[pack contract]** `VERSION` file and `requires_core` in `pack.toml`. `validate` fails and
  `apply` writes nothing when core doesn't satisfy a pack. Packs without it get a warning.
- Unslop and runbook skills, and two honesty rules.
- `ticket-jira` connector and spec-agent campaign mode.
- **[pack contract]** Packs: layered source repos with prefixes, collision checks, hook
  fragments, tripwires, `validate --pack`, and spec-agent extensions (`domains`,
  `intake_context`, `ticket`, `deliver_checks`).
- `aicfg tokens`.
- Core hardening: guard hook bypasses closed, wider secret coverage, hermetic `aicfg` tests,
  CI actions pinned to SHAs.
- spec-agent: 9 agents, domain skills for the DevOps stack, ticket connectors (local,
  GitHub), checkpoint commits at every stop, retro-driven improvements.
- Claude guard hooks and settings merge, validation with cross-references, and tests.
