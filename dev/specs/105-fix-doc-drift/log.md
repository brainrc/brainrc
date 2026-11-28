# Log: 105-fix-doc-drift

## engine · intake
gh:105 via ticket-github, child 2 of 3 in campaign gh:94 (`campaign-094-neutral-core`), branched from 104-local-tripwires. `--oneshot`: `oneshot: true`, `auto: true` from the flag. Size small (doc lines plus one doctor helper; no new dependency), mode inline, domains: scripting, targets: none. Worktree `~/.brainrc-worktrees/brainrc/105-fix-doc-drift`.
Ticket drift since it was written: overrides/README and AGENTS.md wording partly moved; `doctor.py:118` is now three `rm` fixes; the repo is still private.

## engine · Spec gate · auto-approved
5 criteria (AC1–AC5). Defaults: "treat as public" wording; pins match major.minor or use a placeholder; all three `rm` fixes. `living_specs.py check`: exit 0 (new area `doctor`). Plan stage skipped (small).

## engine · verify · T1 attempt 1 failed
`OldNamesTest` flagged `AICFG_HOME` in the new tests/test_doctor_paths.py (old names are allowed only in listed files). Fix: the old-home quoting test moved into tests/test_doctor_home.py, which is on the allow list; plan files updated (wording only, no criterion change).

## code-reviewer · gh:105 batch · done
Inline (review_context: shared). No CRITICAL/HIGH/MEDIUM. 1 LOW: `shell_path` of a path that is exactly the home dir prints `~`; correct for `rm -r` only by intent, and doctor never prints that. Kept.

## engine · verify
720 tests OK (plain and XDG), validate OK (core, acme).

## engine · Deliver gate · auto-approved
2026-11-10T06:18:49Z
Push 105-fix-doc-drift, open a ready PR from pr-body.md against 104-local-tripwires (stacked, Closes #105). Ticket comment stays a draft. No ticket transition.

## engine · watch · review on #264
Inline finding (bxker): `shell_path` built on `tilde()`, which isn't anchored, so a sibling of HOME whose name starts the same printed as `~e/...`. Fixed: `shell_path` works from `Path.relative_to(Path.home())`, with a sibling and a nested-path test (fails on the old helper). Also used for the `validate --pack` and `python3 <hook>` fixes the review named as non-blocking.

## engine · watch · second review on #264
Inline finding (bxker, blocking): the unused-old-home fix suggested `rm -r` even when the old dir contains the settings home or is HOME (`AICFG_HOME=~/.config` gave `rm -r ~/.config`). Fixed: `_held_inside` checks the resolved old dir against HOME, the settings home and the checkout, and the fix then says to keep the dir. Test with `AICFG_HOME` at `~/.config` and at `~`; it fails on the old code. Non-blocking: the stray broken-link scan moved into `_stray_link_findings` and got a quoting test.
