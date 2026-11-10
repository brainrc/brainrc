# Roadmap

The plan lives in GitHub epics: each one groups sub-issues in build order and says how to run
them with spec-agent (`/work --campaign gh:<epic>`). This page lists every open epic by wave,
in the order to start them. A wave is the `Roadmap ID` prefix of the epic's sub-issues (`P0-9`
is wave 0). Within a wave, the epic's own "Start after" note wins over this order.

Shipped work is in the [CHANGELOG](../CHANGELOG.md). Closed epics drop off this page.

## Wave 0: correctness and hygiene
- **E3** [Neutral core and doc drift](https://github.com/brainrc/brainrc/issues/94): keep employer names out of core mechanically, fix stale docs, and keep this page as the epic list.

## Owner decisions
- **D1** [Owner decisions and accounts](https://github.com/brainrc/brainrc/issues/95): the name, the namespace, PyPI and release accounts. A person does these, not spec-agent.

## Wave 1: first run and open source
- **E4** [First-run CLI](https://github.com/brainrc/brainrc/issues/109): an argparse CLI with `init`, `uninstall` and `apply --repair`, touching only installed harnesses.
- **E5** [Harness paths from the environment](https://github.com/brainrc/brainrc/issues/110): read `CLAUDE_CONFIG_DIR`, `CODEX_HOME` and `XDG_CONFIG_HOME` before the default paths.
- **E6** [Open-source readiness](https://github.com/brainrc/brainrc/issues/113): project files, a CI matrix, a README for strangers, and namespaced core skills.

## Wave 2: packs
- **E7** [Pack scaffolding](https://github.com/brainrc/brainrc/issues/114): `new pack`, a pack template repo, and pack author docs.
- **E8** [Item scaffolders](https://github.com/brainrc/brainrc/issues/117): `new skill`, `new agent`, `new rule` and `new command`.
- **E9** [Validation for pack authors](https://github.com/brainrc/brainrc/issues/111): published JSON Schemas, wider validate checks, pack tests, and a reusable validate-pack Action.
- **E10** [Pack extension points](https://github.com/brainrc/brainrc/issues/112): a `[scope]` predicate, declarative guard rules, pack-owned settings keys and reviewers, mode overrides, and unavailable gates.
- **E11** [Guard parity across harnesses](https://github.com/brainrc/brainrc/issues/116): the declarative guard rules evaluated in Cursor, OpenCode, Codex and Antigravity.
- **E12** [Importers](https://github.com/brainrc/brainrc/issues/118): turn CLAUDE.md, AGENTS.md, Cursor, Copilot and Windsurf rules, and Claude plugins into packs.
- **E13** [Facts and freshness](https://github.com/brainrc/brainrc/issues/115): a built-in facts pattern with verified dates, and an audit for stale ones.
- **E14** [pack-builder skill](https://github.com/brainrc/brainrc/issues/122): an interview that plans and generates your own pack, with an eval case.

## Wave 3: split and 1.0
- **E15** [Split and 1.0](https://github.com/brainrc/brainrc/issues/119): split the syncer from spec-agent, freeze the pack API, add profiles, and tag v1.0.
- **E16** [Native Windows](https://github.com/brainrc/brainrc/issues/120): copy mode instead of symlinks, native hook commands, and a Windows CI cell.

## Wave 4: ecosystem
- **E19** [Plugin export and graduation](https://github.com/brainrc/brainrc/issues/123): export a pack as a plugin, plugin dependencies, and a guide for graduating a pack.
- **E20** [Stack packs](https://github.com/brainrc/brainrc/issues/121): reference packs for Python, Node/TypeScript and Rust.
- **E21** [Pack index and pack evals](https://github.com/brainrc/brainrc/issues/124): a searchable pack index, and evals for packs.

## Added after the waves
These have no wave yet; their sub-issues carry no `Roadmap ID`.
- **E17** [Live checks for the native harness packages](https://github.com/brainrc/brainrc/issues/63): run each harness package in a real, logged-in session.
- **E18** [End-to-end sandbox runs](https://github.com/brainrc/brainrc/issues/18): the sandbox tickets in Codex and OpenCode fallback mode, graded by `evals.py check`.
- **E23** [Unattended runs](https://github.com/brainrc/brainrc/issues/241): run budgets, stacked PRs whose run records reach `main`, and concurrent runs.
- **E24** [Repo context and the quality loop](https://github.com/brainrc/brainrc/issues/246): a codemap, lint hooks after edits, core evals in CI, retro lessons promoted to rules, and a second-opinion reviewer.
- **E25** [Third-party plugins, natively](https://github.com/brainrc/brainrc/issues/252): declare and install other people's plugins per harness, with overlap checks.

## Open, with every sub-issue closed
Waiting to be closed:
- **E2** [Config and pack loading](https://github.com/brainrc/brainrc/issues/93): readable config errors first, then the config and pack-loading fixes that build on them.
- **E22** [Rename to brainrc](https://github.com/brainrc/brainrc/issues/199): rename the project and command to brainrc, reading the old names for one minor release.
