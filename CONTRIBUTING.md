# Contributing

Thanks for helping. This page covers setup and how a change gets in. The rules for what a
change may contain live in one place, [AGENTS.md](AGENTS.md), and apply to people and AI
assistants alike. Read it before your first change.

## Setup

```bash
git clone <this-repo> ai-config
cd ai-config
python3 -m pip install pre-commit
pre-commit install
```

You need Python 3.11+. The pre-commit hooks run gitleaks, `aicfg validate`, the tests, and a
check for home-directory paths on every commit.

## Making a change

1. Branch from `main`.
2. Make the change. Content that only fits your team or employer belongs in a pack, not here
   ([packs](docs/packs.md), [tutorial](docs/tutorial.md)).
3. Bump `VERSION` and add your entry under it in `CHANGELOG.md` (the policy is at the top of
   the changelog), then run `python3 scripts/aicfg.py plugin` to update the plugin manifests.
   `validate` fails if any of them disagree.
4. Run the checks:

   ```bash
   python3 scripts/aicfg.py validate
   python3 -m unittest discover -s tests
   ```

   If you changed `docs/tutorial.md` or how `aicfg` installs packs, also run
   `specs/013-tutorial/run-tutorial.sh`.
5. Open a pull request that says why, what changed, and how to verify it, with `Closes #N`
   for the issue. CI runs the same checks.

If another open PR also bumps `VERSION`, the second one to merge takes the next number.

## Using spec-agent

You can let spec-agent do the work: in an AI tool with this repo installed, run
`/work gh:<issue>`. It stops for your approval at the spec, the plan, and delivery. It writes
its record (spec, plan, verification, retro) to `specs/<slug>/`, and that folder ships with
the PR so reviewers can see why each change was made. See [docs/spec-agent.md](docs/spec-agent.md).

## Where things are

Start with the [architecture overview](docs/architecture.md). File formats are in
[docs/formats.md](docs/formats.md).
