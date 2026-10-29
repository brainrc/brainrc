# Verify: Rename the on-disk names kept for compatibility

Run at 2026-10-29T03:05:00Z on commit `acfe7be`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (also with `XDG_CONFIG_HOME=/home/runner/.config`) | pass: OK (1 skipped) both ways |
| Lint | not configured | not configured |
| Build | not configured | not configured |
| Validate (infra) | `python3 scripts/brainrc.py validate` | pass |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | test_mcp `test_an_old_marker_block_is_replaced_once_and_user_content_kept`: asserts the exact file text (block in place, user bytes kept), then that a second apply makes no change. It was red before the in-place rewrite. | pass |
| AC2 | test_mcp `test_codex_block_is_written_with_brainrc_markers`, `test_old_and_new_blocks_together_leave_one_brainrc_block`; `test_an_unterminated_old_block_is_left_alone` (CONFLICT, file unchanged) | pass |
| AC3 | test_brainrc `test_apply_replaces_the_old_guard_link` (also: status in sync, doctor clean), `test_a_real_file_at_the_old_guard_path_is_left_alone`, `test_a_foreign_symlink_at_the_old_guard_path_is_left_alone` | pass |
| AC4 | test_brainrc `test_an_old_record_is_read_then_replaced_by_the_new_one` (status writes nothing; apply adopts with no fetch, red first), `test_apply_leaves_only_a_valid_new_record` (corrupt new record; stale old record), `test_a_mismatching_old_record_still_fetches` | pass |
| AC5 | `tests/test_old_names.py` rows are scoped to `brainrc/mcp.py`, `brainrc/packs.py` and `brainrc/config.py` old-name constants and their tests; the `harnesses.toml` row was removed; suite passes with and without XDG | pass |

## Review
code-reviewer requested changes. All five findings are fixed:
- (blocking) User blank lines were lost around a mid-file old block. The block is now replaced in place.
- A corrupt new record next to a valid old one was never repaired. It is now rewritten on apply.
- A stale old record next to a valid new one was never removed. Apply now removes it.
- Apply could fail on a read-only `.git`. A failed record write is now ignored.
- The unterminated-block behavior was untested. A test now covers it (left alone, CONFLICT).
The foreign-symlink test also asserts that the new link exists.
