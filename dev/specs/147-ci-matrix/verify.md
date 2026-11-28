# Verify: CI matrix, lint and types

Run at 2026-11-03 ~06:19-06:25 (local) on commit `122655e` (branch `147-ci-matrix`, base `146-oss-project-files`). Local host: Linux, default Python 3.13.17; `/usr/bin/python3.11` and `/usr/bin/python3.12` also run where noted. Raw output: `/tmp/claude-0/-home-user/0dcec93d-71ed-51cf-87d5-99510717abc8/scratchpad/verify147/`.

## Checks
| Check | Command | Result |
|---|---|---|
| Tests | `python3 -m unittest discover -s tests` (log `test.log`) | pass: Ran 732 tests, OK (skipped=1), exit 0 |
| Lint | n/a (`state.json` lint: null; ruff not added per spec) | not configured |
| Build | n/a (`state.json` build: null) | not configured |
| Validate | `python3 scripts/brainrc.py validate` (`validate.log`) | pass: `OK: 27 skills, 10 agents, 0 commands`, exit 0; also pass on py3.11 |
| Validate pack | `python3 scripts/brainrc.py validate --pack examples/pack-acme` (`validate-pack.log`) | pass: `OK: 29 skills, 10 agents, 1 commands (packs: acme)`, exit 0 |
| Tutorial check | `python3 scripts/check_tutorial.py` (`check_tutorial.log`) | pass: PASS steps 1-5, exit 0; also exit 0 on py3.11 and py3.12 |
| Sandbox tests | `cd examples/sandbox && python3 -m unittest -q` (`sandbox.log`) | pass: Ran 2 tests, OK, exit 0 |
| Targeted new tests | `python3 -m unittest discover -s tests -v -p 'test_check_tutorial.py'` (`targeted.log`) | pass: 7 tests OK (also py3.11, py3.12) |
| YAML parse | `python3 -I -c "import yaml ..." .github/workflows/validate.yml` (`yaml.log`) | pass: jobs `validate`, `validate-gate`; matrix os 3 x python 3; fail-fast False |
| Gitleaks | `/tmp/claude-0/-home-user-brainrc/0dcec93d-71ed-51cf-87d5-99510717abc8/scratchpad/gl/gitleaks detect --redact -v --exit-code=2 --log-opts="--no-merges --first-parent 146-oss-project-files..HEAD"` (`gitleaks.log`) | pass: 7 commits scanned, no leaks found, exit 0 |
| Pip-install smoke (`check_install.py`) | `python3 -m pip install .` then `check_install.py` | not run: needs network for build isolation (hatchling is not installed locally; `-I -c "import hatchling"` fails). Verify after push in the ubuntu and macOS cells. |
| Matrix cells (9) | GitHub Actions run | verify after push |

## Acceptance criteria
| Criterion | Evidence | Result |
|---|---|---|
| AC1 | YAML parse (`yaml.log`): `os: [ubuntu-latest, macos-latest, windows-latest]`, `python-version: ["3.11","3.12","3.13"]`, `fail-fast: false`. Actual 9-cell run: not observed. | pass (config); cell run verify after push |
| AC2 | Locally run, same commands as CI: `validate`, `validate --pack examples/pack-acme`, `unittest discover -s tests`, sandbox tests (all exit 0, see Checks). Diff keeps these commands unchanged. Pip-install smoke not run locally (no network for build isolation). | partial: pass locally on Linux; pip-install smoke and macOS cell verify after push |
| AC3 | Workflow `if: ${{ !cancelled() && matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12' }}` on the gitleaks step only (diff). Local gitleaks run: no leaks, exit 0. Other steps have no `if`, so they run in every cell. | pass (config and local scan); live single run verify after push |
| AC4 | `continue-on-error: ${{ matrix.os == 'windows-latest' }}` (diff), with a comment giving the reason (`docs/install.md` Platforms). No step is skipped on Windows (only gitleaks is restricted, per AC3). Gate job `validate-gate` (`needs: [validate]`, `if: always()`, `test "$RESULT" = success`) keeps the `validate` check name. Gate behavior when a Windows cell fails: verify after push. The follow-up issue named in the PR description: document stage. | partial: config pass; Windows-failure gate behavior verify after push; PR-body part checked at document stage |
| AC5 | `scripts/check_tutorial.py` run on Linux with py3.11, 3.12, 3.13: PASS steps 1-5, exit 0. Failure paths tested by `test_check_tutorial.py::DocCouplingTest` (changed command, changed heading, missing documented output) and `EndToEndTest::test_real_doc_passes_and_stays_sandboxed` (HOME stays empty, `packs.local.toml` untouched). macOS cell: verify after push. | pass (Linux); macOS cell verify after push |
| AC6 | `test_check_tutorial.py::DocCouplingTest::test_changed_command_fails_naming_step` (edited doc → exit 1, names step 4); `test_changed_heading_fails_parsing`; `test_missing_documented_output_fails` (names step 5). Script reads commands from `docs/tutorial.md` (`steps()`/`parse()`). | pass |
| AC7 | Diff adds no ruff, pyright or coverage config and no new dependency; `changelog.d/147-ci-matrix.md` lists them as deferred pending owner approval. PR description listing them as follow-up: document stage. | partial: pass for "not added"; PR-body part checked at document stage |
| AC8 | `validate` exit 0; unittest 732 tests OK (skipped=1); `changelog.d/147-ci-matrix.md` present with `bump: patch`. | pass |

Constraints from the spec: action pins unchanged by SHA with version comments (diff); `timeout-minutes` and `permissions: contents: read` kept (diff); stdlib-only new script (imports in `scripts/check_tutorial.py` are stdlib); `brainrc/` and `VERSION`/`CHANGELOG.md`/`dist/` untouched (diff stat limited to 4 files).

## Notes
- Post-push, to confirm (not claimed as pass here): all 9 cells green or Windows reported non-blocking; `validate-gate` result when a Windows cell fails. GitHub's `needs.<job>.result` for a matrix job with `continue-on-error` containing a failed cell is not verified offline; if the gate fails on a Windows-only failure, the gate condition needs a change (changes-requested at that point).
- Pip-install smoke: not run locally, network needed for build isolation.
- The one skipped unittest is a guarded test (not identified; run was quiet). Not a criterion-relevant skip.
- Raw logs are outside the repo (scratchpad), per dispatch; `specs/147-ci-matrix/.runs/` was not used.
