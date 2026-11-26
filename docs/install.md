# Install

brainrc is a Python command. The quickest way to get it is [uv](https://docs.astral.sh/uv/getting-started/installation/),
which also fetches a Python 3.11+ if your machine has none. You need git too: brainrc uses it to
fetch packs.

## Install with uv

```bash
uvx brainrc status          # try it first: lists what apply would write, writes nothing
uv tool install brainrc
brainrc apply
brainrc status              # prints "Everything in sync."
```

That's it. `apply` writes into each AI tool installed on this machine and skips the others.
Run `brainrc init` before `apply` if you want to choose which tools brainrc manages, or how much it
installs; [getting started](getting-started.md) walks through it.

If your shell can't find `brainrc` after the install, run `uv tool update-shell` and open a new
shell.

## Other ways to install

| How | Command | Notes |
|---|---|---|
| pipx | `pipx install brainrc` | Same as uv. If `brainrc` isn't found, run `pipx ensurepath`. |
| Homebrew | `brew install brainrc/tap/brainrc` | From the [brainrc/homebrew-tap](https://github.com/brainrc/homebrew-tap) tap. |
| npx | `npx github:brainrc/brainrc status` | Runs brainrc through `uvx`, so it needs uv but no Python. Good for a one-off run, not for `apply`. Keep the `github:`: brainrc isn't on npm. |
| Claude Code plugin | `/plugin install brainrc@brainrc` | Claude Code only, no rules or packs. See [plugins](plugins.md). |
| A clone | `git clone https://github.com/brainrc/brainrc` | For changing brainrc itself. See [below](#from-a-clone). |

Run `apply` from an installed command, not from `uvx` or `npx`: `apply` links your tools into
the installed package, and those two run brainrc from a cache that can be cleared.

## Pin a version

Install a given release with `uv tool install brainrc==<X.Y.Z>` (or `pipx install brainrc==<X.Y.Z>`,
`uvx brainrc@<X.Y.Z>`, `npx github:brainrc/brainrc#v<X.Y.Z>`). Releases are listed on
[PyPI](https://pypi.org/project/brainrc/) and in the [CHANGELOG](../CHANGELOG.md).

## Update

```bash
uv tool upgrade brainrc     # or: pipx upgrade brainrc, brew upgrade brainrc
brainrc apply --repair
```

`--repair` relinks anything that still points at the old version. Moving packs to newer commits
is a separate step, `brainrc update` ([upgrading](upgrade.md)).

<a id="moving-from-ai-config"></a>
Coming from the old names, `ai-config` or spec-agent? [Upgrading](upgrade.md#from-ai-config) has the steps.

## Uninstall

```bash
brainrc uninstall --dry-run     # see what goes
brainrc uninstall               # remove everything apply put into your tools
uv tool uninstall brainrc       # or: pipx uninstall brainrc, brew uninstall brainrc
```

`uninstall` keeps your own settings, hooks and MCP servers, and puts back any instructions file
`init` moved aside. `uninstall --purge` also deletes brainrc's own folder (`~/.config/brainrc`):
your local config and the packs it fetched ([troubleshooting](troubleshooting.md#uninstall)).

## From a clone

Clone brainrc when you want to change brainrc itself. Run the same commands through
`scripts/brainrc.py`:

```bash
git clone https://github.com/brainrc/brainrc ~/brainrc
cd ~/brainrc
python3 scripts/brainrc.py init      # optional: pick tools and a profile
python3 scripts/brainrc.py status
python3 scripts/brainrc.py apply
```

Two things differ from an installed command:

- **Your local files live in the checkout** (`harnesses.local.toml`, `packs.local.toml`,
  `brainrc.local.toml`, `rules/*.local.md`), not in `~/.config/brainrc/`. Git ignores them.
- **Links point into the checkout**, so `git pull` updates every tool at once. Re-run `apply`
  after a pull that changes rules, since rules are rendered, not linked. To stay on a release, check
  out its tag (`git checkout v<X.Y.Z>`) and re-run `apply`.

If you move the checkout, run `python3 scripts/brainrc.py apply --repair` from the new place.
[CONTRIBUTING.md](../CONTRIBUTING.md) covers the checks to run before a pull request.

## Platforms

macOS and Linux. brainrc installs by symlink. On a Windows machine that can't make one (no
Developer Mode, not an administrator), `apply` copies instead and records each copy
([`link_mode`](configuration.md#brainrclocaltoml)), so skills, agents, commands and rules install
without WSL. The hook commands `apply` writes are still POSIX shell, so the guards need WSL
until native Windows hooks land. Those, and a Windows CI cell, are on the [roadmap](roadmap.md).
