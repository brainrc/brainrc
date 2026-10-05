# Spec: Core version contract for packs, and a CHANGELOG

Ticket: gh:5 · Size: standard · Status: approved

## Problem
Packs depend on core's extension API (`pack.toml` `[extensions]`, the rendered `extensions.md`
spec-agent reads, prefix and layout rules). Core has no version, so a pack can't say which core it
was written for, and a breaking change in core silently breaks packs. Pack authors find out only
when spec-agent misbehaves. There is also no record of what changed between core releases.

## Goals
- Core declares a version; packs can declare the core versions they support.
- An incompatible pack is caught by `validate` and blocks `apply` before anything is written.
- Pack authors can see what changed, and which changes affect packs.

## Non-goals
- Pack versions, pack-to-pack dependencies, or resolving/fetching packs.
- Release automation, git tags, or publishing.
- Version checks for harnesses themselves.

## Acceptance criteria
- **AC1**: Given the repo, when a user or `aicfg` asks for the core version, then a single
  canonical value is available (one source of truth), and `validate` fails if it is not a valid
  `MAJOR.MINOR.PATCH` version.
- **AC2**: Given a pack whose `requires_core` core satisfies, when `validate --pack` or `apply` runs,
  then it passes with no version message.
- **AC3**: Given a pack whose `requires_core` core doesn't satisfy, when `validate --pack` (or plain
  `validate` with the pack enabled) runs, then it fails with an error naming the pack, its
  `requires_core`, and the core version.
- **AC4**: Given the same incompatible pack enabled, when `apply` (or `status`) runs, then it exits
  non-zero and writes nothing (no links, renders, or settings changes), with the same message.
- **AC5**: Given a pack without `requires_core`, when `validate` or `apply` runs, then it succeeds
  and prints a warning recommending the field.
- **AC6**: Given a malformed `requires_core` (e.g. `"latest"`, `">>1"`), when `validate` runs, then
  it fails with an error showing the accepted syntax.
- **AC7**: Given a disabled pack, when `apply` runs, then its `requires_core` is not checked.
- **AC8**: `CHANGELOG.md` exists with entries for the current version and history taken from the
  roadmap's Done line; entries that change the pack contract carry a visible marker; the roadmap
  no longer duplicates the Done list.
- **AC9**: `docs/packs.md` documents `requires_core`, its syntax, and the compatibility policy
  (what bumps the version); the `pack.toml` example includes it.
- **AC10**: Tests cover AC2–AC7; the full suite and `validate` pass.

## Constraints
- `scripts/aicfg.py` stays stdlib-only, Python 3.11+ (no `packaging`).
- No behaviour change for existing users with no packs.
- Keep docs short (AGENTS.md).

## Open questions
Each has a recommended default; approving the gate accepts all defaults.
1. **Where does the version live?** Default: a `VERSION` file at the repo root, read by `aicfg`.
   *Matters because* plugin packaging (#26) and humans can read it without parsing Python.
2. **Starting version?** Default: `0.1.0`. *Matters because* `0.x` signals the contract may still
   change; the issue's `">=0.3"` was only an example.
3. **Constraint syntax?** Default: comma-separated clauses with `>=`, `>`, `<=`, `<`, `==`, `!=`
   (e.g. `">=0.1, <0.2"`); a bare version means `>=`. No `~=`/`^`. *Matters because* it's the
   public syntax pack authors write; adding operators later is easy, removing them isn't.
4. **Compatibility policy?** Default: semver; while `0.x`, a breaking pack-contract change bumps
   MINOR, so packs should pin `">=0.N, <0.N+1"`. *Matters because* it tells authors how to pin.
5. **Incompatible pack at `apply`: refuse everything or skip that pack?** Default: refuse
   everything, like name collisions today. *Matters because* skipping would also prune that
   pack's existing links and hooks, a surprising side effect.
