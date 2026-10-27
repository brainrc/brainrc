Point install commands and issue links at brainrc/brainrc

## Why
The repo moved from the old owner's path to `brainrc/brainrc`. Install commands and issue links in
the docs still named the old path and worked only through GitHub's redirect. 1 of 6 in epic #199
(rename to brainrc).

## What changed
- README.md and docs/install.md: clone, `uv tool install`, and plugin marketplace commands use `brainrc/brainrc`.
- docs/harness-packages.md and docs/roadmap.md: issue links use the new repo.
- pyproject.toml: `[project.urls]` with `Repository` and `Issues`.
- Changelog fragment (patch).

## Acceptance criteria
- [x] AC1: no old repo path outside specs/ and CHANGELOG.md, verified by `grep -rn`
- [x] AC2: pyproject lists the new repo and issue URLs, verified by a `tomllib` read
- [x] AC3: manifests regenerate unchanged; validate and 438 tests pass

## How to verify
```
grep -rn "bxker/ai-config" --exclude-dir=specs --exclude-dir=.git --exclude=CHANGELOG.md .
python3 scripts/aicfg.py plugin && git status --porcelain
python3 scripts/aicfg.py validate && python3 -m unittest discover -s tests
```

## Decisions made without you
- Gates auto-approved: Campaign, Spec, Deliver (Plan skipped, size small); see `specs/204-point-urls-brainrc/log.md`
- The ticket names pyproject URLs and the plugin manifests, but none had a URL. Added `[project.urls]`; left the manifests as the plugin command writes them, since #208 rewrites `aicfg/plugin.py`.
- The ticket says 5 doc files; 4 named the old path. Fixed those 4.
- Package name, `ai-config@ai-config`, and the `~/ai-config` clone path stay: #205 and #208 rename them.
- Ticket comment not posted: `specs/204-point-urls-brainrc/ticket-comment.md`

## Follow-ups
- none

Spec: `specs/204-point-urls-brainrc/spec.md` · Plan: `specs/204-point-urls-brainrc/plan.md`
Closes #204
