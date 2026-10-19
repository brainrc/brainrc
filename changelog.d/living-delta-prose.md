---
bump: patch
---
- spec-agent: `living_specs.py` ignores a note before the first `### Area:` under
  `## Requirement changes` (two sandbox runs wrote one, apply rejected it, and the engine edited
  `spec.md` after approval). The engine also runs `living_specs.py check` before presenting the
  Spec gate, so a malformed delta is fixed before it is approved.
