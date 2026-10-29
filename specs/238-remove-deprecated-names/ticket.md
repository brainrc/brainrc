---
id: 238
title: Remove the deprecated aicfg names in 0.5.0
status: in-progress
pr:
---
Follow-up from #199: the deprecation warnings promise that the `aicfg` command, `scripts/aicfg.py`,
`python -m aicfg`, `import aicfg`, `AICFG_HOME` and the legacy `~/.config/ai-config` home are removed
in 0.5.0. Remove them in a `minor` release, keep `brainrc migrate` able to move an old home, and
move the `requires_core` examples to `<0.6`.
