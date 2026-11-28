Run tutorial steps 1-5 in CI and validate on a 3x3 matrix

2 of 4 in epic #113, stacked on #<PREV_PR>. Retarget to `main` before merging.

## Why
CI ran `validate` on ubuntu with Python 3.12 only, so regressions on other Pythons or on macOS went unseen. Nothing checked that the tutorial's commands still work. Windows is documented as unsupported (`docs/install.md`, Platforms), so its cells report but do not block.

## What changed
- `validate` runs on ubuntu, macOS and Windows across Python 3.11, 3.12 and 3.13: 9 cells, `fail-fast` off. Every existing step runs unchanged (bash shell on Windows).
- Windows cells use `continue-on-error`. A failing Windows cell shows green in the checks list; only its logs show the failure.
- Gitleaks runs once, in the ubuntu / 3.12 cell.
- A `validate-gate` job is named `validate`, so the existing check name still exists. It fails unless every blocking cell passes.
- New `scripts/check_tutorial.py` runs tutorial steps 1-5 against a temporary HOME and a copy of the checkout. It fails with the step name when a command exits non-zero or its documented output (`OK:`, `Everything in sync.`) is missing. It reads the commands from `docs/tutorial.md`, so the doc stays the single source. Stdlib only.
- Docs: CONTRIBUTING.md lists the new check; the tutorial says CI runs it.
- Changelog fragment `changelog.d/147-ci-matrix.md` (patch).

## Acceptance criteria
- [ ] AC1: 3 OS x 3 Python matrix, `fail-fast` off; YAML parsed locally, 9 cells after push
- [ ] AC2: same commands as before; `validate`, pack validate, unittest and sandbox pass on Linux; pip-install smoke and macOS cell after push
- [ ] AC3: gitleaks `if:` limited to one cell; config read-through only, live run after push
- [ ] AC4: `continue-on-error` on Windows with a comment; Windows-failure gate behavior after push. Follow-up issue below
- [x] AC5: `check_tutorial.py` passes on Linux (Python 3.11, 3.12, 3.13); macOS after push
- [x] AC6: `tests/test_check_tutorial.py` fails on an edited command, heading or missing output
- [x] AC7: ruff, pyright and coverage not added; listed as follow-up below
- [x] AC8: `validate` and 732 unittest cases pass locally; fragment present

Not run offline: actionlint, zizmor, shellcheck (not installed, no network). The workflow was checked by a YAML parse and a read-through.

## How to verify
```
python3 scripts/brainrc.py validate
python3 scripts/brainrc.py validate --pack examples/pack-acme
python3 -m unittest discover -s tests
python3 scripts/check_tutorial.py
(cd examples/sandbox && python3 -m unittest -q)
```
On the PR's Actions run:
- 9 `validate (<os>, <python>)` cells; the macOS cells run the tutorial check.
- Gitleaks runs only in `ubuntu-latest` / 3.12.
- The pip-install smoke passes on ubuntu and macOS.
- If a Windows cell fails, `validate-gate` should stay green. This is not verified offline. If it goes red on a Windows-only failure, the gate condition needs a change before merge.

## Decisions made without you
- Spec and Plan gates auto-approved (oneshot). The spec was reworked once: the tutorial check covers steps 1-5, because step 4 needs the skill file from step 3.
- Q1: Windows is non-blocking. The ticket's "green on all 9 cells" is not met as written.
- Q2: ruff, pyright and coverage.py not added. They are new dependencies and need owner approval.
- Q3: tutorial steps 6-7 not checked.
- Ticket comment not posted: `specs/147-ci-matrix/ticket-comment.md`.
- Required check: branch protection could not be read (API 403, private repo on the free plan). The `validate` name is kept by the gate job; whether it is required today is unknown.

## Follow-ups
- Issue to file: "Make Windows cells pass and blocking" (not yet created). Promote Windows once its cells pass.
- ruff, pyright, coverage.py: need owner approval of the new dev tools. Until then, the ticket's "coverage reported on PRs" is not met.
- LOW: the HOME-empty assertion in `tests/test_check_tutorial.py` is a smoke check only.
- LOW: `-latest` runner labels float. Pinning them is open.

Closes #147

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01Hn6pdU7RJ1sLQqc3fDP7Sa
