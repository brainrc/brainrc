---
bump: patch
---
- `brainrc check` (#285) exits 1 when anything drifted from `brainrc.lock`, naming each difference:
  a pack added or removed in `brainrc.toml`, a pack file that changed, or an agent file brainrc owns
  in the repo (or its block in `AGENTS.md`) that was edited, removed or added to. It uses no network
  and writes nothing, so CI can run it on a fresh checkout; docs/project.md has a sample Actions
  step. A moved tag is reported as `MOVED` and doesn't fail.
- `check` says whether a drifted file is brainrc's own output for another lock, which
  `install --frozen` updates, or isn't brainrc's, which it refuses without `--force`.
