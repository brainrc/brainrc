---
bump: patch
---
- `brainrc import` reads GitHub Copilot instructions: `.github/copilot-instructions.md` becomes rules, one per section, in order, and path-specific `.github/instructions/*.instructions.md` files become rules (`applyTo: "**"`) or skills with a Domains row for their globs. Each keeps a comment naming its file and lines (#165).
