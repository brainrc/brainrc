# release

How a merge to `main` becomes a version, a tag, and a GitHub Release.

### GitHub Release per version
The release workflow SHALL create a GitHub Release for each `vX.Y.Z` tag it pushes or finds
without one, with that version's `CHANGELOG.md` section as the body, and SHALL NOT create a
duplicate when the release exists. (AC1, AC2, AC3, AC4, AC5)
_Last changed by 218-github-releases._

### No release reaches the removal version early
`validate` and `release` SHALL refuse fragments whose largest bump would release `SHIM_REMOVED_IN` or later while the deprecated names it governs still exist. (AC1)
_Last changed by 236-spec-agent-retro-fixes._
