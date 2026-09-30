---
description: Take a work item from ticket to reviewed PR with spec-agent (gh:<n>, issue URL, local:<path>, or free text)
argument-hint: <gh:42 | issue URL | local:path.md | free text> [--local]
---

Use the `spec-agent` skill to work on this item end to end:

$ARGUMENTS

If a spec for this item already exists under `specs/`, resume it instead of starting over.
If `--local` is given, use `delivery: local-only`: no push, PR, or ticket updates; drafts only.
Stop at every gate for my approval. Never push, open PRs, or update the ticket before the
Deliver gate is approved.
