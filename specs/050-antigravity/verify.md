# Verify: 050-antigravity

| Criterion | Result | Evidence |
|---|---|---|
| AC1 root `plugin.json` generated and checked | pass | `PluginTest` (name-only manifest; `aicfg plugin` writes it; stale/missing check); `plugin.json` committed |
| AC2 rules carry `trigger: always_on`; aicfg strips it; core rules require it | pass | `RuleFrontmatterTest` (strip, render and budget, validate fails without a trigger); red first |
| AC3 no Antigravity guard hooks; README says so | pass | no `hooks.json` at root; README Antigravity block |
| AC4 docs, VERSION 0.3.18, CHANGELOG | pass | README, docs/harness-packages.md, docs/formats.md, roadmap, AGENTS.md |
| AC5 tests, validates, real apply | pass | 132 tests OK; validate core + acme OK; `apply` in a fake HOME renders `instructions.md` byte-identical to main's |

Also: `claude plugin validate .` passes (only the usual CLAUDE.md note); the tutorial script runs
clean; a Codex 0.161.0 reinstall installs 0.3.18 with the root `plugin.json` present.
Not verified: anything against a real `agy` (docs site and installer blocked here).
