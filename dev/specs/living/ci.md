# ci

What the validate workflow must prove on every push and PR.

### Cross-platform validate matrix
The validate workflow SHALL run the repo's checks on ubuntu and macOS for Python 3.11, 3.12 and 3.13 with fail-fast off, run gitleaks once, and report Windows cells without letting them fail the workflow. (AC1, AC2, AC3, AC4)
_Last changed by 147-ci-matrix._

### Tutorial is executed in CI
CI SHALL run an executable check derived from steps 1-5 of `docs/tutorial.md` and fail when a documented command fails or its documented output is missing. (AC5, AC6)
_Last changed by 147-ci-matrix._
