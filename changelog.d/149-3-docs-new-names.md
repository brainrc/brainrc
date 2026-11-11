---
bump: patch
---
- Docs, rules, agents, and skills now use the new core skill names: `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws`, and `brainrc-terraform` (slash commands `/brainrc-work`, `/brainrc-review`, `/brainrc-plan`). The old names `work`, `review`, `plan`, `aws`, and `terraform` remain as deprecated aliases until 0.6.0, when they are removed. `validate` rejects a core skill with a reserved built-in name unless it is a declared deprecated alias. A harness that ignores `disable-model-invocation` (Antigravity) may still list the old names.
