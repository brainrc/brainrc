# Spec: Explicit rule precedence across core, packs, and local rules

Ticket: gh:9 · Size: standard · Status: draft

## Problem
`aicfg` renders rules from core and every enabled pack into one instructions file, interleaved
by filename. A pack's `15-acme.md` lands between core's `10-git.md` and `20-engineering.md`,
and nothing in the rendered file says where a rule came from. Pack authors can't predict the
order, readers can't tell core rules from pack rules, and no doc says what happens when a pack
rule disagrees with a core rule.

## Goals
- A predictable order that doesn't depend on numbering discipline across repos.
- The rendered file shows which source each block of rules came from.
- One documented policy for conflicts.
- `validate` keeps `VERSION` and `CHANGELOG.md` in step, so the every-PR-bumps rule (#30) holds.

## Non-goals
- Detecting contradictions between rules automatically.
- Letting a pack remove or replace a core rule.
- Changing how harnesses load the instructions file.

## Acceptance criteria
- **AC1**: Given core and one or more enabled packs, when `apply` renders instructions, then all
  core rules come first (filename order), then each pack's rules as one block per pack in
  `packs.toml` order (filename order within the pack), then all `*.local.md` rules.
- **AC2**: Given a pack rule named `15-acme.md`, when rendered, then it appears after every core
  rule (no interleaving).
- **AC3**: Given a pack block, when rendered, then it starts with a label naming the pack.
  Local rules are labelled too. Core rules render with no label, as today.
- **AC4**: Given no packs and no local rules, when rendered, then the output is identical to
  today's.
- **AC5**: `docs/packs.md` and `docs/formats.md` state the order and the policy: later rules
  refine earlier ones and must not contradict them. A pack rule that contradicts core is a bug in
  the pack.
- **AC6**: This changes the pack contract: a `## 0.2.0` CHANGELOG entry tagged
  **[pack contract]** (no Unreleased section), `VERSION` bumped to `0.2.0`, and the example
  pack's `requires_core` updated so its test still passes.
- **AC7**: Given a CHANGELOG whose newest `## X.Y.Z` heading differs from `VERSION`, or that
  has an `## Unreleased` heading, when `validate` runs, then it fails with a message naming both
  values (or the Unreleased heading). A matching CHANGELOG passes.
- **AC8**: Full suite, `validate`, and `validate --pack examples/pack-acme` pass.

## Constraints
- Stdlib only. No new config keys.
- The label must not disturb the markdown heading structure of the rules themselves.

## Open questions
Each has a recommended default; approving accepts them all.
1. **Option 1 (number ranges) or option 2 (labelled blocks)?** Default: option 2, as the issue
   suggests. *Matters because* option 1 needs every pack to renumber and a validate rule to
   police it.
2. **Label format?** Default: an HTML comment plus a one-line note, e.g.
   `<!-- pack: acme -->` then `Rules from pack acme. They refine the rules above.` *Matters
   because* a `## Pack: acme` heading would sit above the pack's own `#` headings and break the
   heading hierarchy.
3. **Version?** Default: `0.2.0`. Pack rules move in the rendered file, which can change model
   behavior for existing packs, so it counts as breaking under our policy. *Matters because*
   packs pinned `<0.2` will then need to update their `requires_core`.
