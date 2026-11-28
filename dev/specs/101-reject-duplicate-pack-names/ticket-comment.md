`validate`, `status`, `apply`, and `doctor` now refuse two enabled packs with the same `name` (and a pack named `core`), naming both `packs.toml` keys: ``pack name `acme` is used by both [one] and [two]``. `apply` writes nothing while it stands.
Verify: `python3 -m unittest -v tests.test_aicfg.DuplicatePackTest`.
PR: <PR_URL>
