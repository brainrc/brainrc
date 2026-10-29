---
id: 236
title: spec-agent fixes from the rename campaign's retros
status: in-review
pr: https://github.com/brainrc/brainrc/pull/236
---
From the epic #199 retros: never auto-approve a Spec gate whose living-spec check fails; MODIFIED
blocks carry full requirement text; dispatches quote spec and plan rules verbatim; tests behave
the same locally as on CI with XDG_CONFIG_HOME set; validate refuses a bump that would reach the
shim-removal release while the shims still exist.
