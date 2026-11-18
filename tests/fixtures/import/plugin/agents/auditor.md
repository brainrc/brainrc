---
name: auditor
description: Audits a deploy diff. Use before shipping.
tools: Read, Grep, Glob, mcp__plugin_shipit_tracker__search
model: sonnet
color: red
---

Read the diff and list what could break, using the `deploy` skill's runbook.
