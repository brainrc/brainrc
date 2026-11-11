# Verify: Namespaced core skills with deprecated aliases

Run at 2026-11-03T13:38:52Z on commit `2d96c1c`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 766 ran, OK (skipped=1), exit 0. Log: scratchpad `verify149a/test.log` |
| Targeted | `python3 -m unittest -v tests.test_skill_aliases` | pass: 20 ran, OK, exit 0. Log: `verify149a/targeted.log` |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass: "OK: 32 skills, 10 agents, 0 commands", exit 0 |
| Validate (tutorial) | `python3 scripts/check_tutorial.py` | pass, exit 0 |
| Validate (tutorial readme) | `python3 scripts/check_tutorial.py --readme` | pass, exit 0 |
| Secrets | `gitleaks git --redact --log-opts=149-namespace-core-skills..HEAD .` | pass: no leaks found |
| Apply (AC2) | `HOME=<scratch>/home BRAINRC_HOME=<scratch>/home/.config/brainrc python3 scripts/brainrc.py apply` | pass: `~/.claude/skills/{brainrc-work,brainrc-review,brainrc-plan,brainrc-aws,brainrc-terraform,work,review,plan,aws,terraform}` all symlinks into the worktree. Log: `verify149a/apply.log` |
| Plan / diff | offline only | not applicable |

Skipped test: the full suite reports `skipped=1`; I did not identify it and did not compare against a baseline (`baseline_failures` is empty).

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `test_skill_aliases.NamespacedSkillsTest.test_namespaced_skills_exist_with_matching_name`, `test_work_body_is_unchanged` pass. Manual: `diff` of `git show 149-namespace-core-skills:skills/{aws,terraform}/SKILL.md` body vs `skills/brainrc-{aws,terraform}/SKILL.md` body differs only in the frontmatter `name`/`description` lines | pass |
| AC2 | Manual apply in scratch HOME (see Apply row): both `brainrc-<n>` and `<n>` linked for claude for all five | pass |
| AC3 | `test_every_old_name_is_an_alias_naming_its_replacement_and_removal_release` pass; manual read of `skills/{work,review,plan,aws,terraform}/SKILL.md`: each says "Deprecated", names `brainrc-<n>`, "removed in 0.6.0" (VERSION is 0.5.8, so next minor is 0.6.0), and tells the model to follow the replacement | pass |
| AC4 | `test_user_invoked_aliases_forward_the_same_arguments`, `test_user_invoked_aliases_keep_argument_hint_for_completion` pass. `work` argument-hint unchanged in content. Live `/work` invocation not run (no harness session) | pass |
| AC5 | `test_every_alias_is_model_disabled_with_a_deprecation_description`, `test_each_pair_has_exactly_one_auto_triggerable_member`, `test_knowledge_skills_keep_trigger_description_and_stay_auto_triggerable` pass; manual read: all five aliases have `disable-model-invocation: true` and deprecation descriptions | pass |
| AC6 | `validate` passes (see Checks); tutorial checks pass | pass |
| AC7 | `test_committed_manifests_are_current_and_point_at_a_skills_dir_with_both_names`, `test_generated_plugin_sees_both_names`, `test_stale_manifest_after_adding_skills_fails_validate` pass. Plugin install itself not run | pass |
| AC8 | Near-miss tests pass: `test_alias_missing_disable_model_invocation_fails`, `test_alias_with_the_old_trigger_description_fails`, `test_alias_whose_target_is_missing_fails`, `test_deleted_alias_fails`, `test_alias_not_naming_the_removal_release_fails`, `test_stale_manifest_after_adding_skills_fails_validate`; positive `test_unmodified_copy_validates` | pass |
| AC9 | `validate` exit 0 and full suite exit 0 (see Checks) | pass |

## Notes
- No flaky failures observed; the suite ran once and was green.
- Apply ran with a scratch HOME under the scratchpad, never the real HOME.
- Open spec questions (aws/terraform stubs point to `brainrc-<n>` by reading, not by args; release text is hard-coded to 0.6.0) are not blocking; 0.5.8 in VERSION supports 0.6.0 as the next minor.
- Live slash-command invocation of the aliases (AC4) and plugin install (AC2/AC7) were not run interactively.
