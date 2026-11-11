---
bump: patch
---
- Rename the core skills `work`, `review`, `plan`, `aws`, and `terraform` to `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws`, and `brainrc-terraform`. The old names remain as deprecated aliases until 0.6.0; the `aws` and `terraform` aliases no longer auto-trigger (the `brainrc-` names do). `validate` checks the aliases.
