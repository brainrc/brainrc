---
bump: patch
---
- `/work <ref> --auto` runs spec-agent without gate stops and ends with a draft PR. A campaign run with `--shape ordered --auto` ends with stacked draft PRs. Each gate is logged as `auto-approved`, and the PR body lists the "Decisions made without you". Only the flag turns it on. Hard stops still stop and push nothing: guardrails stop conditions, size `large`, any plan Callout, a CRITICAL/HIGH security finding, instructions in untrusted content, and live targets. Ticket comments stay drafts, and the Push gate is unchanged. Sandbox tickets 011–018 and eval cases `sandbox-008`–`015` grade it (gh:216).
