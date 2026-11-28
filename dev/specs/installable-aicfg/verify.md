# Verify: installable-aicfg

| Criterion | Result | Evidence |
|---|---|---|
| AC1 pyproject, bundled `_core`, version, console script | pass | `uv build`: wheel with `aicfg/` + `aicfg/_core/{skills,agents,rules,overrides,mcp,…}`, no `*.local.*`; installs as `ai-config==0.3.22` with an `aicfg` executable |
| AC2 source detection | pass | `test_bundled_core_is_found_next_to_the_package`; installed venv reports `installed() True`, REPO in site-packages |
| AC3 local files in `$AICFG_HOME`, no writes in the package | pass | `test_local_files_live_in_aicfg_home`, `test_apply_never_writes_inside_the_package`, `test_relative_pack_path_is_relative_to_aicfg_home`, `test_plugin_needs_a_checkout`, `test_copied_roles_are_fine_when_installed`, `test_tokens_match_a_checkout` |
| AC4 real install | pass | `uv tool install git+file://…@installable-aicfg` in a fake HOME: apply, doctor clean, validate OK, plugin refuses (exit 1); vs a checkout run: same instructions.md, extensions.md, OpenCode renders, settings.json, link names; tokens differ only by the checkout's gitignored in-repo extensions.md (43 tokens); pack via relative path in `$AICFG_HOME/packs.local.toml` loads |
| AC5 tests and CI | pass | 151 OK (7 new, red first); CI step simulated in a venv: `pip install .` then `aicfg validate` from outside the repo OK |
| AC6 docs, VERSION 0.3.22, CHANGELOG | pass | README "Install without a clone", docs/packs.md, docs/harness-packages.md, AGENTS.md |

Checkout output unchanged: the fixed-HOME transcript is identical to the 0.3.19 baseline (600 lines).
