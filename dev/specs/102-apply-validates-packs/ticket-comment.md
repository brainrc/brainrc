`apply` and `status` now run the `validate --pack` checks on each enabled pack before linking anything. A pack skill without the pack's prefix (or any other pack error) is printed with `validate --pack <dir>` named, and nothing is written.
Verify: `python3 -m unittest -v tests.test_aicfg.PackApplyCheckTest`.
PR: <PR_URL>
