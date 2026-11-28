# Verify: pack-git

| Criterion | Result | Evidence |
|---|---|---|
| AC1 `git` + `ref`, one of path/git, clone under `$AICFG_HOME/packs` | pass | `test_apply_fetches_and_links`, `test_path_and_git_together_is_an_error` |
| AC2 apply fetches; failure writes nothing; status only reports | pass | `test_apply_fetches_and_links`, `test_failed_fetch_writes_nothing`, `test_status_does_not_fetch`, `test_url_that_looks_like_an_option_is_refused` |
| AC3 `aicfg update` refetches at ref; dirty clone refused | pass | `test_update_moves_to_a_new_ref`, `test_update_leaves_a_changed_clone_alone` |
| AC4 doctor flags unfetched; normal checks after fetch | pass | `test_doctor_flags_an_unfetched_pack`; doctor clean after fetch |
| AC5 offline tests + real run | pass | 8 tests with a local bare repo (7 red first; the option-URL one passed early for an unrelated reason and now guards); real run with uv-installed aicfg: status (no fetch), doctor FAIL, apply FETCH v1 + links, doctor clean, update to v2 links acme-new in all 5 harnesses |
| AC6 docs, VERSION 0.3.23, CHANGELOG | pass | docs/packs.md, packs.toml, README, docs/harness-packages.md |

Also: 159 tests OK; validates, tutorial, `claude plugin validate` OK; the checkout transcript vs the
0.3.19 baseline differs only in the usage text (new `update` line and the pack sentence).
