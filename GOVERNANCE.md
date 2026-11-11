# Governance

brainrc is a small project with one maintainer, `bxker`. The maintainer decides what goes in,
sets direction, and owns releases.

## How changes are accepted

1. Anyone opens a pull request, as described in [CONTRIBUTING.md](CONTRIBUTING.md). The rules for
   what a change may contain are in [AGENTS.md](AGENTS.md).
2. CI must be green (`validate` and the unit tests).
3. A maintainer approves and **squash-merges** it: one commit per change on `main`.

Every merge to `main` is a release; see Releases in CONTRIBUTING.md.

## Disagreements

Discuss on the issue or PR. If there is no consensus, the maintainer makes the call and says why.

## How to become a maintainer

Contribute regularly and well: merged changes, careful reviews, and help on issues. When you have
a sustained record, ask in an issue or let the maintainer invite you. The maintainer decides and
adds you to `.github/CODEOWNERS` and the repo's write access. A maintainer who is inactive for a
long time may step back, and can return on request.

## Conduct and security

Everyone follows the [Code of Conduct](CODE_OF_CONDUCT.md). Vulnerabilities go through
[SECURITY.md](SECURITY.md).
