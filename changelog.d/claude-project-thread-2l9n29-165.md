---
bump: patch
---
- `brainrc import` reads GitHub Copilot instructions: `.github/copilot-instructions.md` becomes rules, one per section, in order, and path-specific `.github/instructions/**/*.instructions.md` files become rules (`applyTo: "**"`) or skills: with a Domains row for their globs, or loaded on request when they have only a description or neither. A file for code review only (`excludeAgent: coding-agent`) is skipped. Each keeps a comment naming its file and lines (#165).
