# Plan: CI matrix and executable tutorial

Spec: [spec.md](spec.md) · Status: approved

## Callouts
- **New dependencies:** none (ruff, pyright, coverage.py stay out: spec safe default, AC7)
- **Public API / contract changes:** none (CLI, hooks, `check_install.py` unchanged)
- **Migrations / data changes:** none
- **Security triggers touched:** CI workflow; `permissions: contents: read`, SHA pins and gitleaks kept
- **Domains:** ci-pipelines, scripting
- **Environments affected on deploy:** none; the workflow change takes effect on push/PR
- **Destructive or replacing changes:** none
- Spec safe defaults applied: Windows non-blocking (Q1), no new tools (Q2), tutorial steps 1, 2, 4, 5 only (Q3).

## Approach
`validate.yml` keeps its one `validate` job and gains `strategy: {fail-fast: false, matrix: {os: [ubuntu-latest, macos-latest, windows-latest], python-version: ["3.11","3.12","3.13"]}}`, `runs-on: ${{ matrix.os }}`, setup-python fed `${{ matrix.python-version }}`, and `continue-on-error: ${{ matrix.os == 'windows-latest' }}` with a comment citing `docs/install.md` Platforms (symlinks, `python3` in hook commands). `defaults: run: shell: bash` lets the existing steps run unchanged on Windows (Git Bash). Every existing step stays, same commands; the gitleaks step gets `if: matrix.os == 'ubuntu-latest' && matrix.python-version == '3.12'` (linux binary, `sha256sum`). A new step runs `python3 scripts/check_tutorial.py`. Pins, `permissions`, `timeout-minutes: 10` stay.

`scripts/check_tutorial.py` follows `scripts/check_install.py` style (docstring with usage, `report()` PASS/FAIL lines, `main() -> int`, crash becomes a FAIL line, temp dir removed in `finally`). `steps(text) -> dict[int, str]` parses `docs/tutorial.md`: each `## N. Title` heading and the first ```` ```bash ```` fence under it, keeping N in {1, 2, 4, 5}; it fails if any is missing. The only substitution is dropping the `git clone ...` line of step 1: instead the script copies the checkout with `shutil.copytree` (ignoring `.git`, `dist`, `__pycache__`, `*.local.*`, `.env*`) to `<tmp>/home/brainrc`, the tutorial's `~/brainrc`. This matters because step 5 writes `packs.local.toml` into the core checkout (`config.local_dir()` is `REPO` when not installed); running in a copy never touches the real repo. Each block runs as `subprocess.run(["bash", "-e", "-o", "pipefail", "-c", block], cwd=<copy>, env=...)`, timeout 120 s, with `HOME`/`USERPROFILE` = temp home, `BRAINRC_HOME` = `<home>/.config/brainrc`, `XDG_CONFIG_HOME` and `PYTHONPATH` dropped. Expected output, which is not a copy of the commands: step 1 has a line starting `OK:`; step 4 has `OK:` and `(packs: myteam)`; step 5 contains `Everything in sync.`. A failure prints `FAIL step N <title>: exit X` plus a stdout/stderr tail. `--doc PATH` (default `docs/tutorial.md`) lets tests point it at an edited copy. argparse, stdlib only.

actionlint, zizmor and shellcheck are not installed here, and there's no network, so the workflow evidence is a YAML parse plus a read-through. macOS and Windows cells only show after push (`verify after push: validate (macos-latest, *)`, `validate (windows-latest, *)`).

## Files
| File | Change |
|---|---|
| `scripts/check_tutorial.py` | new: parse tutorial steps 1, 2, 4, 5 and run them in a temp HOME and checkout copy |
| `tests/test_check_tutorial.py` | new: parser, doc-coupling and end-to-end tests |
| `.github/workflows/validate.yml` | modify: matrix, bash default, Windows continue-on-error, gitleaks `if:`, tutorial step |
| `changelog.d/147-ci-matrix.md` | new: `bump: patch` fragment |

## Risks
- Windows: `python3` may be missing or symlinks may fail. Cells are non-blocking, nothing is skipped; the follow-up issue goes in the PR body.
- The tutorial drifts (e.g. `requires_core` vs `VERSION` 0.5.8). That is the point: the step name shows in the failure.
- Copying the checkout is slow or catches local files. The ignore list covers `*.local.*` and `.env*`; the repo is small.

## Test strategy
`tests/test_check_tutorial.py` loads the script via `importlib` (as `tests/test_evals.py` does). Unit: `steps()` on the real doc returns 1, 2, 4, 5, the step-2 block contains `pack.toml`, step 1 has no `git clone`; a missing step fails. AC6: an edited temp copy of the doc (step 4's `validate --pack` becomes `validate --pak`) run through `main(["--doc", tmp])` exits 1 with `step 4` in the output; an edited expected-step heading fails parsing. AC5: `main()` on the real doc exits 0, and the real checkout has no `packs.local.toml` afterwards if it had none before. Workflow: YAML parse and read-through; matrix cells verified after push.

## Tasks
- [ ] **T1** [agent: implementer] Tutorial check script that reads its commands from the doc
  - files: `scripts/check_tutorial.py`, `tests/test_check_tutorial.py`
  - criteria: AC5, AC6, AC8
  - evidence: `python3 scripts/check_tutorial.py`; `python3 -m unittest discover -s tests`; `python3 scripts/brainrc.py validate`
- [ ] **T2** [agent: implementer] Validate matrix, non-blocking Windows, single gitleaks, tutorial step, changelog
  - files: `.github/workflows/validate.yml`, `changelog.d/147-ci-matrix.md`
  - criteria: AC1, AC2, AC3, AC4, AC5 (CI wiring), AC7, AC8
  - review: each (CI config)
  - after: T1
  - evidence: `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" .github/workflows/validate.yml` (ad hoc, PyYAML present locally, not a dependency); read-through of matrix/`if:`/pins; `python3 scripts/brainrc.py validate` (checks the fragment). actionlint unavailable offline; say so in verify.md.
  - Deliver note: the PR body names the Windows follow-up issue (AC4) and lists ruff/pyright/coverage as a follow-up needing owner approval (AC7).
