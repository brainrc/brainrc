---
bump: patch
---
- The deprecated agent aliases (`analyst`, `verifier` and the rest) now carry their `brainrc-` target's instructions instead of pointing at its file, which a subagent can't locate, so a pack's `reviewer = "infra-reviewer"` still runs the real reviewer until 0.7.0. `validate` fails when an alias's instructions drift from its target's.
- docs/troubleshooting.md lists the new pack naming errors in place of the old prefix message.
- The tutorial, the `pack.toml` example in docs/packs.md and the example packs pin `requires_core = ">=0.6, <0.7"`. The tutorial's old `<0.6` pin failed `scripts/check_tutorial.py` once core reached 0.6.0, and the example packs use `brainrc-infra-reviewer`, which 0.5 lacks.
