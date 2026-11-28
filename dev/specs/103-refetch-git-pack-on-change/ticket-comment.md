`apply` now fetches a git pack again when its `ref` or `git` URL changes, and `status` shows the `FETCH` line first. `doctor` reports a clone that doesn't match its config, and git calls stop after 60 seconds. Clones from older versions are fetched once on the next `apply`.
Verify: `python3 -m unittest -v tests.test_aicfg.GitPackTest`.
PR: <PR_URL>
