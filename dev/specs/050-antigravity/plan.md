# Plan: Antigravity installs ai-config as a plugin

No new dependency or public API change. A new generated file (`plugin.json` at the repo root)
and a format change to core rules (frontmatter, stripped by aicfg) are called out in AGENTS.md.

## Approach
- `rule_text(path)`: a rule's text without frontmatter. `render_instructions` (core, pack and local
  rules) and `always_tokens` use it, so rendered output and budgets don't change.
- `_validate_source` for core: each `rules/*.md` needs `trigger` in its frontmatter.
- `plugin_manifests()` adds `plugin.json` = `{"name": "ai-config"}`; `check_plugin` and
  `cmd_plugin` already loop over its keys.

## Tasks
| id | title | agent | files | criteria |
|---|---|---|---|---|
| T1 | tests first: strip, trigger check, root plugin.json | implementer | tests/test_aicfg.py | AC1, AC2 |
| T2 | aicfg: rule_text, trigger check, plugin.json | implementer | scripts/aicfg.py | AC1, AC2 |
| T3 | core rules get `trigger: always_on`; regenerate manifests | implementer | rules/*.md, plugin.json | AC2 |
| T4 | real `apply` in a fake HOME | implementer | none | AC5 |
| T5 | docs and release | implementer | README.md, docs/*, AGENTS.md, VERSION, CHANGELOG.md | AC3, AC4 |
