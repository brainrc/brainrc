# Security policy

## Guard model

brainrc ships hooks that prompt for or block risky commands. They match command text, so they
are a **seatbelt**: they catch accidents and skipped gates, not a determined bypass. The real
boundary is the **credentials** a run holds. Keep admin and write-capable credentials out of the
shell. The layers and the documented **Known gaps** are in [docs/guardrails.md](docs/guardrails.md).

## What to report

Report these:

- A risky command a guard pattern claims to catch (see `overrides/claude/hooks/`) that runs
  without a prompt or block, using plain, unaliased command text.
- A hook, script, or generated file that leaks a secret or writes outside its intended paths.
- A flaw in how brainrc installs or syncs files that lets untrusted content run code.

Not a vulnerability: a gap already listed under Known gaps in [docs/guardrails.md](docs/guardrails.md),
such as aliases, wrappers, indirect execution, or credentials already in the environment.
Open a normal issue or PR for those.

## How to report

Report privately: open the repo's **Security** tab and choose **Report a vulnerability**, or go to
<https://github.com/brainrc/brainrc/security/advisories/new>. Do not use public issues or PRs for
a suspected vulnerability. Include the command or file, what you expected, and what happened.

## Supported versions

Only the latest release is supported. Fixes land on `main` and ship in the next release.

## What to expect

This is a volunteer-run project. The maintainer will read each report, reply in the advisory, and
tell you whether it is accepted. No response time is promised. We will credit you in the release
notes if you want.
