<!-- divio: how-to -->
# Validate a pack in its own CI

Check a pack on every push and before each commit, against the brainrc version it pins.

The `validate-pack` action checks a pack against the core version you pin, and against core's
default packs (Gatework) at the versions that core pins, so a pack may use their skills and agents:

```yaml
- uses: actions/checkout@<sha>
- uses: brainrc/brainrc/.github/actions/validate-pack@<core tag or sha>
  with:
    path: .                  # the pack's directory (default: the repository root)
    # default-packs: "false" checks it against core alone
    # python-version: "3.12" sets one up; by default it uses the python3 on PATH
```

The ref you pin is the core: GitHub runs the action from that commit of this repository, so
there is nothing else to clone. To check before each commit, add the pre-commit hook, which
installs `brainrc` at the `rev` you pin:

```yaml
- repo: https://github.com/brainrc/brainrc
  rev: <core tag>
  hooks:
    - id: brainrc-validate-pack
      # args: [pack]          # the pack's directory, when it isn't the repository root
```

Both run `validate --pack <dir> --fetch-defaults`, which fetches the default packs at the refs
core's `packs.toml` pins into clones of their own under `$BRAINRC_HOME/validate-packs/` (once;
later runs reuse them), never the clones `apply` links.

Without either, clone core at the version you pin and run it yourself:

```bash
git clone --depth 1 --branch <core tag> https://github.com/brainrc/brainrc core
python3 core/scripts/brainrc.py validate --pack . --fetch-defaults
```

What `validate --pack` checks is listed in the [reference](../packs.md#what-validate-checks).
