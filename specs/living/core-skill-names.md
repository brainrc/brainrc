# core-skill-names

Core skill names are namespaced, never shadow reserved names, and old names get a deprecation window.

### Namespaced core skills
The system SHALL ship `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws` and `brainrc-terraform`. (AC1, AC7, AC8)
_Last changed by 149-3-docs-new-names._

### Deprecated aliases
The system SHALL keep `work`, `review`, `plan`, `aws` and `terraform` working through one minor release, each printing a deprecation note, and SHALL NOT let an alias double an auto-trigger. (AC2, AC3, AC5)
_Last changed by 149-3-docs-new-names._

### Reserved names
`validate` SHALL fail on a core skill that has a reserved built-in name and is not a declared deprecated alias. (AC4, AC6)
_Last changed by 149-3-docs-new-names._
