# Changelog

The core version lives in [`VERSION`](VERSION). Packs pin it with `requires_core`
([docs/packs.md](docs/packs.md#compatibility)).

Entries tagged **[pack contract]** change what packs can rely on: `pack.toml` keys and
extensions, the rendered `extensions.md`, naming and layout rules. While the version is `0.x`,
a breaking pack-contract change bumps MINOR. After `1.0`, it bumps MAJOR. Everything else
(new skills, fixes, docs) bumps PATCH.

Every merged PR bumps `VERSION` and adds its entries under that version. There is no Unreleased
section: `main` is what users pull, so `VERSION` must always describe it exactly.

## 0.3.5 (2026-10-06)

- `scripts/evals.py`: `check` grades a finished spec-agent run against a case file (two sandbox
  cases included), and `triggers` scores skill selection from descriptions with any model CLI.
  Packs can add their own cases. Offline tests run in CI (#6).

## 0.3.4 (2026-10-06)

- Docs: `CONTRIBUTING.md` covers setup, the change workflow, and spec-agent use. The rules stay
  in `AGENTS.md`, linked both ways (#15).

## 0.3.3 (2026-10-06)

- Docs: `docs/tutorial.md` builds a pack with one domain skill from a fresh clone, linked from
  the README. Every command in it is checked by running the tutorial itself (#13).

## 0.3.2 (2026-10-05)

- Docs: `docs/architecture.md` with one diagram, an install-time vs run-time table, and a
  glossary, linked from the README (#14).

## 0.3.1 (2026-10-05)

- spec-agent, from the first five run retros (#33): sizing counts changed lines, not just
  files; intake warns about other open PRs that bump `VERSION`; intake names `fallback` mode
  and how to install the agents; the Deliver gate lists code changes before spec artifacts;
  gates record when they were presented and approved so retros split agent time from waits;
  `code-reviewer` checks user-facing text against the docs.

## 0.3.0 (2026-10-05)

- **[pack contract]** Ticket connector contract in `skills/spec-agent/references/connectors.md`.
  `validate` fails when a connector (a core `ticket-*` skill or a pack's
  `[extensions.ticket].connector`) has no `##` heading for `fetch`, `comment`, `transition`,
  or `link_pr`. Packs: check your connector, and update `requires_core` to `">=0.3, <0.4"`.
- Packs keep one ticket connector each, now documented.
- `ticket-github` works through the GitHub MCP server when `gh` isn't available.

## 0.2.1 (2026-10-05)

- **[pack contract]** `ticket-jira`: `review_status`, `in_progress_status`, and `blocked_status`
  accept a table keyed by project key, with an optional `"*"` fallback (#4). Non-breaking: a
  plain status name still works.
- `ticket-jira`: task-list checkboxes post to Jira as escaped text, so use ✅ / ⬜ bullets (#4).
- Docs: README states per-harness support, stale Jira and machine-specific notes removed.

## 0.2.0 (2026-10-05)

- **[pack contract]** Rule order: core rules first, then each pack's rules as a labelled block
  in `packs.toml` order, then `*.local.md` rules under their own label. Pack rules no longer
  interleave with core rules by filename. Packs: re-check your rules read correctly after
  core's, and update `requires_core` to `">=0.2, <0.3"`.
- `validate` fails when the newest CHANGELOG heading doesn't match `VERSION`, or when an
  `## Unreleased` section exists.

## 0.1.1 (2026-10-05)

- `doc-types` skill: classify a doc as one Divio type (tutorial, how-to, reference,
  explanation), write to that type's shape, and split mixed docs. `doc-writer` and `runbook`
  use it.
- Example pack in `examples/pack-acme`, validated by a test and in CI.

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
