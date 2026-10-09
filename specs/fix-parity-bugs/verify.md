# Verify: fix-parity-bugs

| Criterion | Result | Evidence |
|---|---|---|
| AC1 dangling `*.md` link | pass | `test_dangling_markdown_link_in_a_skill_is_reported`: validate exit 1 with "dangling symlink", tokens exit 0 |
| AC2 invalid fragment | pass | `test_invalid_fragment_stops_apply_before_writing` (nothing in HOME), `..._is_a_doctor_finding`, `..._in_plugin_and_validate` (ERROR; error printed once) |
| AC3 unknown `agents_format` in doctor | pass | `test_unknown_agents_format_is_a_doctor_finding` |
| AC4 hook event order | pass | `test_new_hook_events_keep_fragment_order` (8 new events, order kept) |
| AC5 red first; suite; unchanged output | pass | 6 new tests failed first (5 crashes, 1 order); 144 OK; validates, tutorial, `claude plugin validate` OK; fixed-HOME transcript identical to the 0.3.19 baseline (600 lines) |
