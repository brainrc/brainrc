# Spec: core agents under brainrc-

Ticket: gh:295 · Size: standard · Status: approved

## Problem
Core skills moved under `brainrc-` in 0.5.14, but the ten agents still take generic names such as
`verifier`, which a pack or another plugin can collide with.

## Goals
- The ten core agents are `brainrc-<old name>`, and every reference that names one uses the new name.
- The old names keep working until 0.7.0.

## Non-goals
- Changing what any agent or spec-agent does. Prose that says "the implementer" stays.

## Acceptance criteria
- **AC1**: Given `agents/`, then each of the ten agents is `agents/brainrc-<name>.md` with that `name`, and
  spec-agent's role table, Domains table, dispatch lines, plan template, references and docs name the new ones.
- **AC2**: Given an old name, then `agents/<name>.md` is a short alias whose description starts
  `Deprecated`, whose `tools` and `model` match its target, and whose body names the target and 0.7.0.
- **AC3**: Given a missing alias, an alias whose tools, model, description or body is off, or a new core
  agent without `brainrc-`, then validate fails; the shipped tree and a new `brainrc-` agent pass.
- **AC4**: Given a pack with `reviewer = "infra-reviewer"`, then validate still accepts it.

## Requirement changes
### Area: core-skill-names
#### ADDED: Namespaced core agents
The system SHALL ship its ten agents as `brainrc-*`, keep the old names as deprecated aliases with the
same tools and model until 0.7.0, and `validate` SHALL fail on a missing or divergent alias or an
unprefixed new core agent. (AC1, AC2, AC3, AC4)

## Open questions
None. Defaults taken under the auto run:
1. The epic's naming rules are a breaking [pack contract] change, so the release bumps minor to 0.6.0
   and "one minor release" means the aliases go in 0.7.0.
2. An agent can't forward its arguments like a skill alias can, so the alias keeps the target's tools
   and model and tells the agent to read the target file next to it and follow it.
