<!-- divio: how-to -->
# Import the instruction files you have

Move a `CLAUDE.md`, `AGENTS.md`, Cursor rules or Copilot instructions into a pack in one command.

`brainrc import PATH ...` writes the instruction files you already have as a pack, so they move
over in one command. A folder means the files in it that brainrc reads.

| Source | Becomes |
|---|---|
| `CLAUDE.md`, `AGENTS.md` | one rule per section, in order |
| Cursor: `.cursor/rules/**/*.mdc`, `.cursorrules` | `alwaysApply: true` rules and `.cursorrules` become rules; a rule scoped by `globs` becomes a skill with a row in Gatework's Domains table for those globs; one with only a `description` becomes a skill with that description |
| Copilot: `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md` | copilot-instructions.md becomes one rule per section; a path-specific file with `applyTo: "**"` becomes a rule, one scoped to other globs a skill with a Domains row, one with neither a skill loaded on request, as for Cursor; one for code review only (`excludeAgent: coding-agent`) is skipped |

Each file is split at the shallowest heading level it uses more than once (a lone `# Title`
stays with the text under it), and each part becomes `rules/NN-<heading>.md` with a first-line
comment naming the file and lines it came from. Headings inside code blocks don't count. A
CLAUDE.md line that is only `@path` (Claude Code's import) is replaced by that file's rules, and
a brainrc project block is left out, since `install` writes it.

```bash
brainrc import ~/.claude/CLAUDE.md --name mine --enable   # write ~/.config/brainrc/imported/mine, load it
brainrc import . --to tools/agent-pack --dry-run          # what a repo's files would become
```

The pack goes to `$BRAINRC_HOME/imported/<name>` unless `--to` names a folder, and is checked as
`validate --pack` would. `import` never overwrites a folder with files in it; `--force` replaces
an earlier pack there (a folder with a `pack.toml`), never one that holds a source. `--enable` adds it to `packs.local.toml`; for one project, list it in `brainrc.toml` instead
([team setup](../project.md)).
