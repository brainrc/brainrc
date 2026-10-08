# Changelog

The core version lives in [`VERSION`](VERSION). Packs pin it with `requires_core`
([docs/packs.md](docs/packs.md#compatibility)).

Entries tagged **[pack contract]** change what packs can rely on: `pack.toml` keys and
extensions, the rendered `extensions.md`, naming and layout rules. While the version is `0.x`,
a breaking pack-contract change bumps MINOR. After `1.0`, it bumps MAJOR. Everything else
(new skills, fixes, docs) bumps PATCH.

Every merged PR bumps `VERSION` and adds its entries under that version. There is no Unreleased
section: `main` is what users pull, so `VERSION` must always describe it exactly.

## 0.3.15 (2026-10-08)

- Docs: `docs/harness-packages.md` records the #50 spike: what each harness (Claude Code, Codex,
  Gemini CLI, OpenCode, Cursor) supports for native packages, rules, hooks, agents, and packs,
  with sources, unconfirmed items, and a proposed build order. The roadmap drops shipped items.

## 0.3.14 (2026-10-07)

- Claude Code plugin: `/plugin marketplace add bxker/ai-config`, then
  `/plugin install ai-config@ai-config`, installs the skills, agents, commands, and guard hooks
  without `aicfg`. Rules, packs, and other harnesses still need `aicfg`. `aicfg plugin` generates
  `.claude-plugin/` from the repo, and `validate` fails when it's stale, so run it after every
  `VERSION` bump. Packs stay `aicfg` packs (decision in `docs/packs.md`) (#26).

## 0.3.13 (2026-10-07)

- spec-agent: in subagent mode, independent plan tasks (no `after:` dependency, no shared
  files) run as parallel waves in separate git worktrees and land in plan order; at most 2
  per wave for `standard`, 3 for `large`. State and the retro record the time saved. Sandbox
  ticket 003 and `evals/cases/sandbox-003.toml` exercise it (#25).
- spec-agent: gates are asked as a multiple-choice question (Approve / Request changes, plus
  any open choices) when the harness has one, e.g. Claude Code's `AskUserQuestion`.

## 0.3.12 (2026-10-07)

- Supported platforms documented: macOS and Linux, Windows through WSL or with symlinks
  enabled. `skills/spec-agent/roles` stays a symlink; `validate` and `doctor` now say when a
  checkout broke it and how to restore it (#11).

## 0.3.11 (2026-10-07)

- **[pack contract]** `validate` enforces always-loaded token budgets (rules plus descriptions)
  per source: 3,000 for core, and a pack's optional `max_always_tokens` in `pack.toml`.
  Non-breaking: a pack without the key gets a warning above 1,000 tokens, and any description
  over 100 tokens gets a warning. `tokens` shows each source against its budget (#10).
- `unslop`: the rule catalogue moves word for word into `references/`, so SKILL.md is ~1.5k
  tokens instead of ~3.5k, with a 60-token description. `doc-types` description trimmed.

## 0.3.10 (2026-10-07)

- spec-agent, from the #39, #12, #17, and #42 retros (#44): the verifier runs anything a person
  runs once for real, with a fresh fake `HOME`; the implementer shows red by switching off only
  the new change; the done checkpoint is pushed after CI on the delivered commit finishes; test
  lines count about half toward size.

## 0.3.9 (2026-10-07)

- `apply` removes ai-config's hooks from a disabled harness's settings file (other hooks and
  settings stay, backup first), and `doctor` reports them until it does. Uninstalling no longer
  needs a manual step (#42).

## 0.3.8 (2026-10-07)

- Docs: `docs/troubleshooting.md`, by symptom: missing items, `CONFLICT`, pack errors, settings
  backups, uninstalling, and reporting a guard hook mistake. `doctor` points to it when it finds
  a problem (#17).

## 0.3.7 (2026-10-06)

- `aicfg doctor`: a read-only check of this machine's install. It reports stale renders,
  missing, wrong, stale, or broken links, broken or incompatible packs, unmerged hooks, and
  harnesses that aren't installed, each with its fix, and exits 1 on any problem (#12).
- `aicfg` on Python older than 3.11 prints one line saying so instead of a traceback.

## 0.3.6 (2026-10-06)

- Sandbox fixes from the first E2E run (#18): a `.gitignore` so setup and test runs leave a clean
  tree, and a decoy `.env` that the new `canary` eval check proves never leaked. `sandbox-002`
  uses it. The `main_untouched` check's PASS message no longer reads "expected".

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
