---
bump: patch
---
- `validate` and `release` refuse changelog fragments whose bump would release the version that
  removes the deprecated `aicfg` names (`SHIM_REMOVED_IN`) while those names still exist.
- spec-agent: an auto Spec gate is never approved while `living_specs.py check` fails;
  dispatches quote spec and plan rules word for word; the analyst writes MODIFIED blocks as the
  requirement's full new text. Tests clear `XDG_CONFIG_HOME`, so they behave the same locally as
  on CI.
