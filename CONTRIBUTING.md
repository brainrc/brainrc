# Contributing

Thanks for helping. This page covers setup and how a change gets in. The rules for what a
change may contain live in one place, [AGENTS.md](AGENTS.md), and apply to people and AI
assistants alike. Read it before your first change.

## Setup

```bash
git clone <this-repo> brainrc
cd brainrc
python3 -m pip install pre-commit
pre-commit install
```

You need Python 3.11+. The pre-commit hooks run gitleaks, `brainrc validate`, the tests, and a
check for home-directory paths on every commit.

To keep your employer's or clients' names out of the repo, list them in `tripwires.local.toml`
at the repo root. Git ignores the file, and `validate` fails on any tracked file that contains
one of the terms, in its name or text, ignoring case:

```toml
terms = ["Initech", "initech.internal"]
```

## Making a change

1. Branch from `main`.
2. Make the change. Content that only fits your team or employer belongs in a pack, not here
   ([packs](docs/packs.md), [tutorial](docs/tutorial.md)).
3. Add a changelog fragment, `changelog.d/<branch>.md`, with its `bump` (`patch` or `minor`,
   policy at the top of `CHANGELOG.md`) and your entry ([format](changelog.d/README.md)).
   Don't edit `VERSION` or `CHANGELOG.md`; the release does. If `validate` says the plugin
   manifests or package.json are stale (you changed hooks), run `python3 scripts/brainrc.py plugin`.
4. Run the checks:

   ```bash
   python3 scripts/brainrc.py validate
   python3 -m unittest discover -s tests
   python3 scripts/check_tutorial.py
   ```

   If you changed `docs/tutorial.md` or how `brainrc` installs packs, also run
   `specs/013-tutorial/run-tutorial.sh`.
5. Open a pull request that says why, what changed, and how to verify it, with `Closes #N`
   for the issue. CI runs the same checks.

PRs are **squash-merged**: one commit per change on `main`, titled by the PR. A spec-agent
branch's checkpoint commits stay on the branch; its `specs/<slug>/` folder carries the record.

## Releases

Every merge to `main` is a release. `.github/workflows/release.yml` runs
`python3 scripts/brainrc.py release`, which folds the fragments into `CHANGELOG.md`, bumps
`VERSION` by the largest `bump`, and regenerates the plugin manifests and package.json. It then commits
`Release vX.Y.Z` and tags `vX.Y.Z`, then creates a GitHub Release for the tag with that version's
`CHANGELOG.md` section as its notes (`python3 scripts/brainrc.py release --notes X.Y.Z` prints them).
It then builds the sdist and wheel from the tag (`scripts/check_dist.py` checks them), attaches
them to the GitHub Release, and publishes them to [PyPI](https://pypi.org/project/brainrc/) by
trusted publishing: the `pypi` job runs in GitHub environment `pypi` with an OIDC token, and the
workflow holds no PyPI token. Last, it writes `Formula/brainrc.rb` for the release
(`scripts/homebrew_formula.py`, pointing at the PyPI sdist), installs and tests it with Homebrew,
and pushes it to [brainrc/homebrew-tap](https://github.com/brainrc/homebrew-tap) over HTTPS with the
token in secret `HOMEBREW_TAP_TOKEN` (fine-grained, Contents read and write on the tap only); without
that secret the step skips with a notice. Each run works on the
version in `VERSION` at `main`'s tip: a tag without a release, a missing asset or a missing PyPI
upload of that version gets it on the next run, or when you run the workflow by hand (**Actions →
release → Run workflow**). If publishing fails, run it again before the next merge; once `VERSION`
moves on, the earlier version stays off PyPI. Users pin a tag ([install](docs/install.md)). If `main` is
protected, add GitHub Actions to the rule's bypass list so the workflow can push its release
commit and tag.

After each release, the `docs` workflow builds the docs site from the new tag (`mkdocs.yml`, one
version per minor release with mike) and pushes it to the `gh-pages` branch. GitHub Pages serves
it at https://brainrc.github.io/brainrc/.
Preview locally with `pip install --require-hashes -r .github/docs-requirements.txt && mkdocs serve`.

Gatework, the default pack, is released the same way from
[brainrc/gatework](https://github.com/brainrc/gatework). To ship a new Gatework release with
core, bump `ref` under `[gatework]` in `packs.toml` to its tag, in a PR with its own fragment.

Before merging a PR whose fragment says `bump: minor` (or one that moves the Gatework `ref` in
`packs.toml`, which changes spec-agent's roles, references, or templates), run the sandbox evals in Claude Code and grade them
([evals](docs/evals.md)). Record the run in [docs/e2e-runs.md](docs/e2e-runs.md). Unit tests
show that the syncer works, and only evals show that the agent still behaves.

## Using spec-agent

You can let spec-agent do the work: in an AI tool with this repo installed, run
`/brainrc-work gh:<issue>`. It stops for your approval at the spec, the plan, and delivery. It writes
its record (spec, plan, verification, retro) to `specs/<slug>/`, and that folder ships with
the PR so reviewers can see why each change was made. See [docs/spec-agent.md](docs/spec-agent.md).

## Where things are

Start with the [architecture overview](docs/architecture.md). File formats are in
[docs/formats.md](docs/formats.md).
