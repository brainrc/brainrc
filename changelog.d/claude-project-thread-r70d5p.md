---
bump: patch
---
- **[pack contract]** Packs pin the pack API now, a version of its own (`PACK_API`, 1.0, in
  `brainrc/packapi.py`), with `requires_api = "^1"`. Core releases that change only content leave
  it alone, so the pin survives them. Constraints take `^` too. `new pack`, the pack template and
  the example packs write `requires_api` (#174).
- **[pack contract]** `requires_core` is deprecated. It still works: alone, it is checked against
  core's version as before, and `validate --pack` warns; beside `requires_api` it is ignored, left
  for older cores. It goes no sooner than pack API 2.
- docs/packs.md#compatibility writes down what pack API 1 freezes and the policy: MINOR adds,
  MAJOR removes or changes, and a deprecation warns for at least one core minor release first.
  docs/schemas/pack-api/1.0.json is the frozen list, and a test fails when the contract changes
  without `PACK_API` moving (`scripts/pack_api.py --write` freezes a new version).
