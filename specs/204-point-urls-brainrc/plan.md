# Plan: Point URLs and manifests at brainrc/brainrc

Spec: [spec.md](spec.md) · Status: approved

## Callouts
Must be empty or explicitly approved at the Plan gate:
- **New dependencies:** none
- **Public API / contract changes:** none
- **Migrations / data changes:** none
- **Security triggers touched:** none
- **Domains:** none (docs and metadata)
- **Environments affected on deploy:** none
- **Destructive or replacing changes:** none

## Approach
Replace `bxker/ai-config` with `brainrc/brainrc` in the four docs (install lines and issue
links; issue numbers survive a transfer). Add `[project.urls]` to `pyproject.toml`. Run the
plugin command to confirm the manifests are current, then validate and test.

## Files
| File | Change |
|---|---|
| `README.md`, `docs/install.md`, `docs/harness-packages.md`, `docs/roadmap.md` | modify: new repo path |
| `pyproject.toml` | modify: add `[project.urls]` |
| `changelog.d/204-point-urls-brainrc.md` | new: patch fragment |

## Risks
- A redirect-only URL left behind, mitigated by AC1's grep.

## Test strategy
AC1 by grep, AC2 by `tomllib` read, AC3 by plugin regeneration plus validate and the suite.

## Tasks
- [ ] **T1** [agent: implementer] Point docs and pyproject at brainrc/brainrc
  - files: `README.md`, `docs/install.md`, `docs/harness-packages.md`, `docs/roadmap.md`, `pyproject.toml`, `changelog.d/204-point-urls-brainrc.md`
  - criteria: AC1, AC2, AC3
