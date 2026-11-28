# Spec: Point URLs and manifests at brainrc/brainrc

Ticket: gh:204 · Size: small · Status: approved

## Problem
The repo moved from `bxker/ai-config` to `brainrc/brainrc`. Install commands and issue links
in the docs still name the old path and work only through GitHub's redirect, which breaks if
anyone ever creates a repo at the old name. New users copy these lines first.

## Goals
- Every install command and issue link outside `specs/` and `CHANGELOG.md` names `brainrc/brainrc`.
- PyPI metadata names the new repo.

## Non-goals
- Renaming the package, command, plugin, or settings home (#205-#208); `ai-config@ai-config`,
  `uv tool upgrade ai-config`, and `~/ai-config` clone paths stay.
- Editing `specs/` or `CHANGELOG.md` history.

## Acceptance criteria
- **AC1**: Given the repo, when `grep -rn "bxker/ai-config"` runs outside `specs/`, `.git/`
  and `CHANGELOG.md`, then it finds nothing.
- **AC2**: Given `pyproject.toml`, when its `[project.urls]` is read, then `Repository` and
  `Issues` point at `https://github.com/brainrc/brainrc`.
- **AC3**: Given the change, when `python3 scripts/aicfg.py plugin` regenerates the manifests,
  then `git diff` shows no manifest change and `validate` and the test suite pass.

## Constraints
Docs and metadata only. No behavior change.

## Requirement changes
None.

## Open questions
1. The ticket lists "pyproject.toml project URLs" and the plugin manifests, but none of them
   name a URL today. *Default taken (auto):* add `[project.urls]` `Repository` and `Issues` to
   pyproject (AC2); leave the manifests' fields as the plugin command generates them (AC3), since
   adding a repo field there means changing `aicfg/plugin.py`, which #208 rewrites.
2. The ticket says 5 doc files; 4 name the old path (README.md, docs/install.md,
   docs/harness-packages.md, docs/roadmap.md). *Default:* fix those 4; AC1 is the check.

## Proposed split
