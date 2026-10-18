---
bump: patch
---
- spec-agent: dispatch puts the skills a role file names on a new `Role skills:` line with
  absolute paths (doc-writer: pr-description, doc-types, unslop, runbook; security-reviewer:
  security-checklist). Roles have no skill tool, so the doc-writer couldn't load them.
- spec-agent: `specs/<slug>/.runs/` ignores itself with its own `.gitignore` (`*`) instead of
  an intake edit to `.git/info/exclude`, which Claude Code protects and every E2E run was denied.
