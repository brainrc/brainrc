<!-- divio: how-to -->
# Keep your own instructions in a pack

Move the instructions you wrote for yourself into a pack, so every AI tool on every machine you
use gets them, and brainrc's own files stay untouched.

## 1. Start from what you have

If you already keep instructions in a `CLAUDE.md`, an `AGENTS.md`, Cursor rules or Copilot
instructions, import them; each section becomes a rule ([import](import.md)):

```bash
brainrc import ~/.claude/CLAUDE.md --name mine --to ~/src/mine --enable
```

Otherwise, start an empty one and turn it on:

```bash
brainrc new pack mine --to ~/src/mine --enable
```

## 2. Keep it short

Rules load into every session. Put a habit you want everywhere in `rules/`, and anything longer
(how you like a commit message, a checklist) in a skill that loads when it's needed.
`brainrc tokens` shows what each costs ([context cost](../packs.md#context-cost)).

## 3. Carry it to your other machines

Push the folder to a repository (private, if you like), then on each machine:

```toml
# packs.local.toml
[mine]
git = "git@github.com:you/mine.git"
```

```bash
brainrc apply
```

Leave out `ref` to follow the default branch: `brainrc update mine` then takes your latest
commits ([use a pack](use-a-pack.md)).
