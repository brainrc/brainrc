---
bump: patch
---
- A pack's CI can check it in one step: `uses: brainrc/brainrc/.github/actions/validate-pack@<core
  tag>` runs `validate --pack` against the core at that tag and the default packs that core pins
  (`default-packs: "false"` skips them). `.pre-commit-hooks.yaml` adds the `brainrc-validate-pack`
  hook, which does the same with the `brainrc` installed at the `rev` you pin. Both use the new
  `validate --pack <dir> --fetch-defaults`, which fetches the default packs at the refs core's
  `packs.toml` pins into clones of their own, never the ones `apply` links. Core's CI checks both
  example packs with the action, and the install smoke test runs a pack's tests from the
  installed package (#139).
