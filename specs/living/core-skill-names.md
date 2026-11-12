# core-skill-names

Core skill names are namespaced, never shadow reserved names, and old names get a deprecation window.

### Namespaced core skills
The system SHALL ship `brainrc-work`, `brainrc-review`, `brainrc-plan`, `brainrc-aws` and `brainrc-terraform`. (AC1, AC7, AC8)
_Last changed by 149-3-docs-new-names._

### Reserved names
`validate` SHALL fail on a core skill that has a reserved built-in name. (AC2)
_Last changed by 292-remove-skill-aliases._

### Namespaced core agents
The system SHALL ship its ten agents as `brainrc-*`, keep the old names as deprecated aliases with the
same tools and model until 0.7.0, and `validate` SHALL fail on a missing or divergent alias or an
unprefixed new core agent. (AC1, AC2, AC3, AC4)
_Last changed by 295-brainrc-agents._
