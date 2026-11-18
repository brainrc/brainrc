<!-- divio: how-to -->
# Share a pack with a team through its repository

Give every agent that opens one repository the same rules and skills, on every machine and in CI,
whether or not each person has brainrc installed.

## 1. Write the pack into the repository

From the repository's root:

```bash
brainrc new pack team --to tools/agent-pack
```

It prints the `brainrc.toml` table that loads it. Delete the pack's
`.github/workflows/validate.yml` and `.pre-commit-config.yaml`: they only run at a repository's
root, and step 4 checks the pack from this repository's CI. A pack your team keeps in its own
repository works the same way with `git` and `ref` in place of `path`.

## 2. List it in `brainrc.toml`

```toml
version = 1

[packs.team]
path = "tools/agent-pack"
```

## 3. Apply and commit

```bash
brainrc apply
git add brainrc.toml brainrc.lock tools/agent-pack .agents .claude AGENTS.md CLAUDE.md
git commit -m "Add the team's agent pack"
```

`apply` writes the pack's skills into the repository (`.agents/skills/`, `.claude/skills/`) and its
rules into `AGENTS.md`, and records every file's hash in `brainrc.lock`
([team setup](../project.md)).

## 4. Check it in CI

Add both checks to the repository's CI: the pack against brainrc, and the agent files against the
lock.

```yaml
- uses: brainrc/brainrc/.github/actions/validate-pack@<brainrc tag>
  with:
    path: tools/agent-pack
- run: pipx run brainrc check
```

After a change to the pack, run `brainrc apply` again and commit the new lock with it; `check`
names any file that differs ([drift in CI](../project.md#checking-for-drift-in-ci)).
