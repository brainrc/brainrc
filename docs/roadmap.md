# Roadmap

The plan lives in GitHub epics: each one groups sub-issues in build order and says how to run
them with Gatework (`/brainrc-work --campaign gh:<epic>`). This page lists every open epic
under the release gate it belongs to, matching the GitHub milestones, in the order to start them.
Within a gate, the epic's own "Start after" note wins over this order. An epic whose children
span two gates sits under the gate where most of its open work is, and its line names the child
that sits elsewhere.

A sub-issue's `Roadmap ID` says where it belongs: `GA-`, `GB-` or `GC-` for Gate A, B or C, and
`P0-` to `P4-` for the earlier waves 0 to 4, which the gates replaced.

Shipped work is in the [CHANGELOG](../CHANGELOG.md). A closed epic drops off the lists; each
gate's first line names the epics it has shipped.

## Gate A: public launch
Shipped in this gate: E4, E5, E6, E27 (lockfile), E28 (trust baseline) and E29 (pack naming).
Gate A's standalone issues, with no epic, are in its
[milestone](https://github.com/brainrc/brainrc/milestone/1).
- **D1** [Owner decisions and accounts](https://github.com/brainrc/brainrc/issues/95): the name, the namespace, PyPI and release accounts. A person does these, not an agent.

## Gate B: v1.0
Shipped in this gate: E16 (native Windows).
- **E30** [Evals as a product](https://github.com/brainrc/brainrc/issues/301): `brainrc eval` with and without a pack, project token budgets, and a 30% cut in core's always-loaded tokens. Its MCP tool budgets child (#332) is Gate C.
- **E7** [Pack scaffolding](https://github.com/brainrc/brainrc/issues/114): `new pack`, a pack template repo, and pack author docs.
- **E8** [Item scaffolders](https://github.com/brainrc/brainrc/issues/117): `new skill`, `new agent`, `new rule` and `new command`.
- **E12** [Importers](https://github.com/brainrc/brainrc/issues/118): Windsurf rules and Claude plugins as packs, after the Gate A importers for CLAUDE.md, AGENTS.md, Cursor and Copilot.
- **E10** [Pack extension points](https://github.com/brainrc/brainrc/issues/112): a `[scope]` predicate, declarative guard rules, pack-owned settings keys and reviewers, mode overrides, and unavailable gates.
- **E11** [Guard parity across harnesses](https://github.com/brainrc/brainrc/issues/116): the declarative guard rules evaluated in every tool, compiled to OS sandbox settings, and a security-baseline pack.
- **E31** [Adapter SDK and more tools](https://github.com/brainrc/brainrc/issues/305): an adapter plugin interface, then Copilot, Gemini CLI, Windsurf, Kiro, Amp and Junie.
- **E20** [Stack packs](https://github.com/brainrc/brainrc/issues/121): official packs (starter, review, Go, Terraform, Kubernetes, Python, Node/TypeScript, Rust) as folders of [brainrc/packs](https://github.com/brainrc/packs), and domain skills moved out of core.
- **E15** [Split and 1.0](https://github.com/brainrc/brainrc/issues/119): freeze the pack API, move `specs/` out of the way, and tag v1.0. Its README and concepts child (#296) is Gate A.
- **E21** [Pack index and pack evals](https://github.com/brainrc/brainrc/issues/124): evals for packs, a searchable index, signing tiers, a publish scanner and badges. Its verified vendor packs child (#333) is Gate C.
- **E14** [pack-builder skill](https://github.com/brainrc/brainrc/issues/122): an interview that plans and generates your own pack, with an eval case.

## Gate C: team adoption
- **E32** [Teams and org policy](https://github.com/brainrc/brainrc/issues/324): an org manifest, a `brainrc check` GitHub Action, and an agent bill of materials.
- **E33** [Cloud and parallel agents](https://github.com/brainrc/brainrc/issues/328): cloud agents and devcontainers set up from the lockfile, and loaded config verified by hash.
- **E13** [Facts and freshness](https://github.com/brainrc/brainrc/issues/115): a built-in facts pattern with verified dates, and an audit for stale ones.
- **E19** [Plugin export and graduation](https://github.com/brainrc/brainrc/issues/123): export a pack as a plugin, plugin dependencies, and a guide for graduating a pack.
- **E23** [Unattended runs](https://github.com/brainrc/brainrc/issues/241): run budgets, stacked PRs whose run records reach `main`, and concurrent runs.
- **E24** [Repo context and the quality loop](https://github.com/brainrc/brainrc/issues/246): a codemap, lint hooks after edits, retro lessons promoted to rules, and a second-opinion reviewer. Its core-evals-in-CI child (#249) is Gate B.
- **E25** [Third-party plugins, natively](https://github.com/brainrc/brainrc/issues/252): declare and install other people's plugins per harness, with overlap checks.
- **E17** [Live checks for the native harness packages](https://github.com/brainrc/brainrc/issues/63): run each harness package in a real, logged-in session.
- **E18** [End-to-end sandbox runs](https://github.com/brainrc/brainrc/issues/18): the sandbox tickets in Codex and OpenCode fallback mode, graded by `evals.py check`.

## Open, with every sub-issue closed
Waiting to be closed:
- **E2** [Config and pack loading](https://github.com/brainrc/brainrc/issues/93): readable config errors first, then the config and pack-loading fixes that build on them.
- **E3** [Neutral core and doc drift](https://github.com/brainrc/brainrc/issues/94): keep employer names out of core mechanically, fix stale docs, and keep this page as the epic list.
- **E9** [Validation for pack authors](https://github.com/brainrc/brainrc/issues/111): published JSON Schemas, wider validate checks, pack tests, and a reusable validate-pack Action.
- **E22** [Rename to brainrc](https://github.com/brainrc/brainrc/issues/199): rename the project and command to brainrc, reading the old names for one minor release.
- **E26** [One-line install](https://github.com/brainrc/brainrc/issues/275): uvx, pipx, Homebrew and npx installs, with a CI check on time to first `status`.
