---
bump: patch
---
- `/work --oneshot` runs a ticket with no manual intervention and ends in ready PRs, never merged. A `large` ticket splits into a stacked campaign, and plan Callouts take the safer default, listed under "Decisions made without you". Tainted stops (a CRITICAL/HIGH security finding, an instruction in untrusted content, a secret) push nothing, as with `--auto`; benign stops (retry budget, scope breach, spec gap, no safe default) open a draft `[blocked] <ticket ref>: <reason>` PR.
- Eval cases `sandbox-016`–`031` grade oneshot runs; the eval `campaign` check gains `ready` and an optional `order`.
