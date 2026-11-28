The release workflow now creates a GitHub Release for each `vX.Y.Z` tag, using that version's `CHANGELOG.md` section as its notes. It skips a release that already exists, so re-runs are safe. `aicfg release --notes X.Y.Z` prints the notes.
Verify: `python3 -m unittest -v tests.test_aicfg.ReleaseTest`.
PR: <PR_URL>
