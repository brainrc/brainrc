# Verify: Make the repo public

Run at 2026-11-01T05:10Z on commit `a558097`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` | pass: 703 ran, 0 failed, 1 skipped |
| Tests (XDG) | `XDG_CONFIG_HOME=/home/runner/.config python3 -m unittest discover -s tests` | pass: 703 ran, 0 failed, 1 skipped |
| Lint | none | not configured |
| Build | none | not configured |
| Validate (infra) | `brainrc.py validate`; `--pack examples/pack-homelab`; `--pack examples/pack-acme` | pass: all three OK |
| Plan / diff | none | offline only |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | `HomelabGuardTest.test_core_no_longer_asks`; `GuardOutwardTest.test_asks_for_outward_and_destructive` still has `sudo reboot`, `sudo halt` | pass |
| AC2 | `HomelabGuardTest.test_pack_asks_for_destructive`, `test_pack_allows_read_only`, `test_pack_ignores_other_tools_and_bad_payloads` | pass |
| AC3 | `ExamplePackTest.test_homelab_pack_is_valid_without_warnings`; `HomelabGuardTest.test_pack_fragment_runs_hook_from_its_hooks_dir` | pass |
| AC4 | `docs/guardrails.md` core list: reboot/poweroff only, links `examples/pack-homelab/README.md` | pass |
| AC5 | `rg -n '(/Users/\|/home/)[A-Za-z0-9_.-]+' . \| grep -v /home/runner` → 0 lines | pass |
| AC6 | `skills/spec-agent/references/state.md` `worktree` row: "home directory written as `~`" | pass |
| AC7 | gitleaks 8.24.3 (sha256 checked against CI's pin), `gitleaks git --redact --log-opts=--all`: 789 commits, "no leaks found"; same with `--gitleaks-ignore-path /dev/null` | pass |
| AC8 | `rg -i bxker --glob '!CHANGELOG.md' --glob '!specs/**' .` → 0 lines | pass |

## Notes
- The gitleaks scan covers non-merge commits (gitleaks' `git log -p` default). 907 commits exist, and merges add no content beyond their parents unless a conflict resolution introduced it.
- The history contains a personal author email in commit metadata, which gitleaks does not check. Listed as a follow-up for the owner.
- T2 (a mechanical path replacement plus one doc line) was reviewed by the engine inline, not by a separate reviewer.
