# Plan: Namespaced core skills with deprecated aliases

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** additive. New skills/commands `brainrc-{work,review,plan,aws,terraform}`; old names stay as aliases until 0.6.0. Only behavior change: `aws`/`terraform` aliases stop auto-triggering (their `brainrc-` twins take over).
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** scripting
- **Environments affected on deploy:** none (users get it on next `brainrc apply` / plugin update)
- **Destructive or replacing changes:** none

## Approach
`git mv skills/<n> skills/brainrc-<n>` for the five, then change only `name:` in each moved `SKILL.md`. Write a new short `skills/<n>/SKILL.md` alias: `description` is a deprecation notice ("Deprecated: use brainrc-<n>; removed in 0.6.0"), `disable-model-invocation: true`, `argument-hint` copied for work/review/plan, body tells the model to follow the `brainrc-<n>` skill with `$ARGUMENTS` (work/review/plan) or to read `brainrc-<n>` (aws/terraform). The 0.6.0 text is fixed (log: engine resolved Q3), so `VERSION` is untouched.

AC2 and AC7 hold by construction: `brainrc apply` links every dir from `sources.skills()` (`config.KINDS`), and `plugin.plugin_manifests()` points at `./skills/` instead of listing skills, so `.claude-plugin/`, `.cursor-plugin/` and `plugin.json` don't change. `check_plugin()` already fails stale manifests (`PluginTest.test_validate_fails_on_missing_or_stale_manifests`). No regeneration needed. If a manifest diff ever shows up, run `python3 scripts/brainrc.py plugin`; never hand-edit.

To make the AC5 near-miss real, add `_check_aliases()` to `brainrc/validate.py`, called from `_validate_source` for core: a `DEPRECATED_ALIASES = {"work": "brainrc-work", ...}` table. Each alias must set `disable-model-invocation: "true"`, have an existing target, and name that target and `0.6.0` in its body. Validate already resolves old-name references (`SKILL_MENTION`, Domains `../aws/SKILL.md` links, pack `domains`) because the alias dirs still exist (AC6).

## Files
| File | Change |
|---|---|
| `skills/brainrc-{work,review,plan,aws,terraform}/SKILL.md` | git mv from old dir; `name:` only |
| `skills/{work,review,plan,aws,terraform}/SKILL.md` | new alias stubs |
| `brainrc/validate.py` | `DEPRECATED_ALIASES` + `_check_aliases()` |
| `tests/test_skill_aliases.py` | new contract tests |

Old-path references that keep working through the alias dirs, left unchanged (149.3 repoints docs/evals): `tests/test_planning.py:37` (`skills/plan`: alias keeps `disable-model-invocation` + `argument-hint` flags), `tests/test_brainrc.py:231,739,829,1254` (dir still exists, `skills/work` still a token label), `skills/spec-agent/SKILL.md:54` Domains links, `evals/triggers.toml` + `tests/test_evals.py` `domain_skills()` (still `aws`/`terraform`), the `` `aws` skill`` mentions in `guardrails.md` and `security-checklist`, and `docs/spec-agent.md:41`, `docs/efficiency.md:14`, `README.md:24,30`.

## Risks
- Always-loaded token budget: core is at 2656/3000, and five alias descriptions get added. Mitigated by keeping each alias description at 80 characters or fewer (about 100 tokens total). `BudgetTest` and `validate` enforce the limit.
- Trigger evals (live model runs) would see both the alias and `brainrc-aws`. The alias is model-disabled, and 149.3 updates `triggers.toml`.
- The alias body must also respect `UserInvokedSkillTest`: any alias with `$ARGUMENTS` keeps `disable-model-invocation` + `argument-hint`.

## Test strategy
Unit tests in `tests/test_skill_aliases.py`. On the real repo: AC1 (dirs, `name`, `brainrc-plan` keeps the old argument-hint/flags), AC3/AC5 (alias text, flags, `brainrc-aws`/`brainrc-terraform` have no `disable-model-invocation`), AC7 (`check_plugin() == []`, and the cursor manifest's `skills` dir contains both names). Near-misses use `TempRepoCase` from `tests/test_brainrc.py`: an alias with `disable-model-invocation` removed fails `cmd_validate`, an alias whose target is missing fails, and a stale manifest after `set_core_version` fails `check_plugin`. Then run the full suite plus `validate` (AC9).

## Tasks
- [ ] **T1** [agent: test-writer] Contract tests for the namespaced skills and aliases (red until T2)
  - files: `tests/test_skill_aliases.py`
  - criteria: AC1, AC3, AC4, AC5, AC7, AC8
  - review: each
- [ ] **T2** [agent: implementer] git mv the five skills, write alias stubs, and add `_check_aliases` to validate
  - files: `skills/work/`, `skills/review/`, `skills/plan/`, `skills/aws/`, `skills/terraform/`, `skills/brainrc-work/`, `skills/brainrc-review/`, `skills/brainrc-plan/`, `skills/brainrc-aws/`, `skills/brainrc-terraform/`, `brainrc/validate.py`, `changelog.d/149-1-namespaced-skills.md` (`bump: patch`; AGENTS.md requires one fragment per PR)
  - criteria: AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC9 (T1 green; `python3 scripts/brainrc.py validate` OK; full suite passes; `git status` shows no change under `.claude-plugin/`, `.cursor-plugin/`, `plugin.json`)
  - review: each
  - after: T1
