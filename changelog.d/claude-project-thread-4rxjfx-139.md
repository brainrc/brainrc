---
bump: patch
---
- A pack's CI can check it in one step: `uses: brainrc/brainrc/.github/actions/validate-pack@<core
  tag>` runs `validate --pack` against the core at that tag, after fetching core's default packs
  (`default-packs: "false"` skips them). `.pre-commit-hooks.yaml` adds the `brainrc-validate-pack`
  hook, which runs the `brainrc` installed at the `rev` you pin. Core's CI checks both example packs
  with the action, and the install smoke test runs a pack's tests from the installed package (#139).
