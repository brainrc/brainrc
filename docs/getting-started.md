# Getting started

This page takes you from nothing to a working setup, then adds a rule of your own. It takes about
ten minutes. It assumes you [installed](install.md) the `brainrc` command; from a clone, run
`python3 scripts/brainrc.py` wherever this page says `brainrc`.

## 1. Choose what to install (optional)

```bash
brainrc init
```

`init` asks four things, then shows how many files, hooks and tokens the result costs before it
writes anything:

1. **Which tools to manage.** It lists the AI tools it finds (a tool counts as installed when its
   folder exists, such as `~/.claude` or `~/.codex`) and saves your answer in
   `harnesses.local.toml`.
2. **Whether to adopt your instruction files.** If you already wrote `~/.claude/CLAUDE.md` or
   `~/.codex/AGENTS.md`, brainrc can't link its own file there. `init` copies your text into a
   local rule, which every tool then loads, and moves the original aside as
   `<file>.bak-brainrc-<time>`.
3. **Whether to install each default pack**, such as Gatework. Your answer goes in
   `packs.local.toml` ([default packs](packs.md#default-packs)).
4. **How much to install**, as a starter profile:

    | Starter | Installs |
    |---|---|
    | `minimal` | rules only |
    | `app` | rules, skills, agents, commands and guard hooks, without Gatework's Terraform, AWS, Kubernetes and GitOps skills |
    | `infra` | everything, MCP servers included |

Run in a project folder, `init` also offers to turn that project's `CLAUDE.md`, `AGENTS.md`,
Cursor rules and Copilot instructions into a pack ([import](packs.md#import)).

`init` never runs `apply`. You can skip it: without it, brainrc manages every tool it finds and
installs everything. `brainrc init --yes` takes those defaults without asking.

## 2. Preview

```bash
brainrc status
```

```text
FETCH     gatework  https://github.com/brainrc/gatework.git (v0.8.0)
CREATE    claude    ~/.claude/CLAUDE.md
CREATE    claude    ~/.claude/hooks/brainrc
CREATE    claude    ~/.claude/skills/brainrc-work
...
CREATE    codex     ~/.codex/AGENTS.md
MERGE     claude    ~/.claude/settings.json  (hooks)
Skipped, not installed: opencode (~/.config/opencode), antigravity (~/.gemini/config), cursor (~/.cursor). ...

Dry run. Run `apply` to write.
```

Each line is one change, then the tool and the path:

| Word | Means |
|---|---|
| `FETCH` | download a git pack (here Gatework, the default pack) |
| `CREATE`, `UPDATE` | add or refresh a link or a rendered file |
| `MERGE` | add brainrc's hooks or MCP servers to a settings file, keeping yours |
| `PRUNE` | remove a link to something no longer installed |
| `PERMS` | a pack adds (`+`) or drops (`-`) a hook, MCP server, tool grant or network domain; `apply` asks first |
| `CONFLICT` | a file brainrc didn't write is in the way; brainrc leaves it alone ([fix](troubleshooting.md#conflict-in-status-or-apply)) |

## 3. Apply

```bash
brainrc apply
brainrc status
```

The second `status` prints `Everything in sync.` Start a new session in your AI tool to pick up
the changes. Here is what landed, for Claude Code:

| What | Where | How |
|---|---|---|
| Rules | `~/.claude/CLAUDE.md` | a link to the rendered `~/.config/brainrc/instructions.md` |
| Skills, agents | `~/.claude/skills/`, `~/.claude/agents/` | one link per item |
| Guard hooks | `~/.claude/settings.json` | merged in, with a backup of the file first |
| The lock | `~/.config/brainrc/brainrc.lock` | each pack's commit and each file's hash |

Other tools get the same content in their own places ([what reaches each tool](capabilities.md)).
`brainrc audit` lists everything each tool now loads and where it came from.

## 4. Try it

In Claude Code, ask for something the guard hooks watch, such as `git push`: Claude Code asks you
before it runs. Type `/brainrc-work` with a sentence describing a small change to try
[Gatework](gatework.md).

## 5. Add a rule of your own

Local rules are markdown files ending in `.local.md` in `~/.config/brainrc/rules/` (from a clone:
`rules/` in the checkout). They load after all the others, in every tool:

```bash
mkdir -p ~/.config/brainrc/rules
echo "- Answer in British English." > ~/.config/brainrc/rules/90-spelling.local.md
brainrc apply
```

Rules are rendered into one file, so every change to a rule needs `apply`. Until then, `status`
lists `~/.config/brainrc/instructions.md` as `UPDATE`. For more than a rule or two, or to share
them, make a [pack](packs.md): a folder or git repo of your own rules and
skills. [Your first pack](tutorial.md) builds one step by step.

## 6. Check the install

```bash
brainrc doctor
```

`doctor` changes nothing. It prints `No problems found.` or names each problem with its fix:
broken links, stale rules, hooks that can't run, a pack that isn't fetched.

## Next

- Turn Gatework off, or pin it: [packs](packs.md#default-packs).
- Give a repo's agents a shared, pinned setup: [team setup](project.md).
- Every command and option: [commands](commands.md).
