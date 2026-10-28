# Changelog fragments

Each PR adds one file here instead of editing `VERSION` or `CHANGELOG.md`. On merge to `main`,
the release workflow runs `python3 scripts/brainrc.py release`. That folds every fragment into
`CHANGELOG.md` under the next version, bumps `VERSION` by the largest `bump`, regenerates the
plugin manifests, and tags `v<VERSION>`.

Name the file after your branch (`living-specs.md`). Format:

```markdown
---
bump: patch
---
- What changed and why, as one changelog bullet (several bullets are fine).
```

`bump` follows the policy at the top of `CHANGELOG.md`: `patch` for new skills, fixes, and docs;
`minor` for a breaking **[pack contract]** change while core is `0.x`. `validate` checks every
fragment.
