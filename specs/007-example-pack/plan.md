# Plan: Example pack validated in CI

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none
- **Public API / contract changes:** none (example only, never enabled by default)
- **Migrations / data changes:** none
- **Security triggers touched:** CI workflow (one added `run:` step, no new inputs or permissions)
- **Domains:** ci-pipelines
- **Environments affected on deploy:** CI only: the `validate` job gains one step
- **Destructive or replacing changes:** none
- **Spec deviation:** `intake_context` must name a skill, so the pack has two prefixed skills
  (`acme-deploy` for the domain, `acme-context` for intake), not one. Using a core skill there
  would teach the wrong pattern.

## Approach
Mirror the layout in `docs/packs.md` exactly, so the example and the doc can't disagree:
`pack.toml` (`requires_core = ">=0.1, <0.2"`, all four extension points, `ticket-jira` with
`refs = ["ACME-*"]`, `host = "acme.example.net"`), `skills/acme-deploy/SKILL.md` in the
domain-skill shape (Validate / Conventions / Review checklist / Never without approval),
`skills/acme-context/SKILL.md` (what to fetch at intake), `rules/50-acme.md`,
`commands/acme-release-notes.md` (uses `$ARGUMENTS`), and `tripwires.toml`. The tripwire bans a
retired tool name, and the rule mentions it once on a line its `allow` pattern passes, so the
example shows both halves. README: copy, rename prefix, enable, validate in the pack's own CI.

Reuse `cmd_validate(pack)` for the test: a new `ExamplePackTest` in `tests/test_aicfg.py` runs it
against `REPO / "examples/pack-acme"` with the real `VERSION`, asserting exit 0 and no `WARN`.
This is what fails on a core bump outside `requires_core` (AC4). The workflow gets a separate
named step after core validate, so a failure is labelled clearly in the checks list.

## Files
| File | Change |
|---|---|
| `examples/pack-acme/**` | new: pack.toml, README.md, 2 skills, 1 rule, 1 command, tripwires.toml |
| `tests/test_aicfg.py` | modify: `ExamplePackTest` |
| `.github/workflows/validate.yml` | modify: one step, `validate --pack examples/pack-acme` |
| `docs/packs.md` | modify: link to the example near the top |
| `CHANGELOG.md` | modify: `## Unreleased` entry (untagged) |

## Risks
- The example's `requires_core` pins `<0.2`, so the next contract bump (#8, #9) fails the test
  until the example is updated. That is intended (AC4): the bump PR updates the example too.
- Example text trips gitleaks or the no-home-paths hook, mitigated by using only `acme` names
  and reserved `example.net` hosts.

## Test strategy
`ExamplePackTest` (AC1, AC2 via validate's own checks, AC4). AC4 also checked by mutating
`VERSION` to `0.2.0` in a temp copy and seeing the test fail. AC5: verify after push from the
PR's `validate` job. AC7: full suite and core `validate` unchanged.

## Tasks
- [ ] **T1** [agent: implementer] Example pack plus `ExamplePackTest`
  - files: `examples/pack-acme/**`, `tests/test_aicfg.py`
  - criteria: AC1, AC2, AC3, AC4, AC7
- [ ] **T2** [agent: implementer] CI step, docs link, CHANGELOG entry
  - files: `.github/workflows/validate.yml`, `docs/packs.md`, `CHANGELOG.md`
  - criteria: AC5, AC6
