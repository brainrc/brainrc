# Troubleshooting

Start here: this lists what's wrong with the install on this machine and how to fix each item.
It changes nothing.

```bash
python3 scripts/aicfg.py doctor
```

Then find the symptom below.

## A harness doesn't see a skill, agent, command, or rule

Run `python3 scripts/aicfg.py apply`. Skills, agents, and commands are symlinks, so edits to
existing ones show up at once, but new or removed ones need `apply`. Rules are different:
they're rendered into `~/.config/ai-config/instructions.md` (or `$AICFG_HOME`), so **every** change to `rules/` (or a pack's
rules) needs `apply`, edits included. Restart the harness or start a new session afterwards.

If you moved the repo, the old links are broken. `doctor` names each one: delete it, then
`apply`.

## Every skill shows up twice, or a hook runs twice

Both the Claude Code plugin and `aicfg` are installed. Keep one: `/plugin uninstall
ai-config@ai-config`, or uninstall `aicfg` (below).

## `CONFLICT` in `status` or `apply`

A real file, or a symlink pointing outside this repo and your packs, sits where `aicfg` wants
a link. `aicfg` never overwrites it. Look at it, then either:

- move it into the repo or a pack (as a skill, agent, or command) and delete the original, or
- delete it if you don't need it,

and run `apply` again. `CONFLICT` on a settings file means it isn't valid JSON: fix it by
hand. `CONFLICT` naming an MCP server means your harness config already defines a server of that
name: rename or remove yours (or the registry's), then run `apply`.

## Pack errors

| Message | Fix |
|---|---|
| ``skill `acme-deploy` is defined in both acme and acme2`` | Rename one. Each pack's items carry its own `prefix`. |
| ``acme:skills/x: pack skills must start with `acme-` `` | Rename the item to start with the pack's `prefix`. |
| ``acme:pack.toml: `prefix` must be lowercase-hyphenated and end with '-'`` | Fix `prefix` in `pack.toml`, e.g. `acme-`. |
| ``acme:pack.toml: requires_core `>=2.0` is not satisfied by core 1.2.3`` | Update core (`git pull`) or the pack, or set `enabled = false` for it in `packs.local.toml`. |
| `pack acme: no pack.toml at ...` | Fix the pack's `path` in `packs.local.toml`. |

`validate` reports all of these. `apply` writes nothing while a name collision or a
`requires_core` mismatch stands. See [packs.md](packs.md).

## Settings backups

Before `apply` changes a harness's settings file (Claude Code: `~/.claude/settings.json`), it
copies it next to the original as `settings.json.bak-aicfg-<UTC time>`. The last 5 are kept.
No backup is made when the file didn't exist yet. MCP config files (`~/.claude.json` and the
others) are backed up the same way.

The rewritten file and its backup keep the original's permissions, so a `0600` `~/.claude.json`
stays `0600`. If the path is a symlink (a dotfiles-managed `settings.json`), `apply` writes
through to the link's target and leaves the link in place; the backup goes next to the target.

## Apply while something else writes

Close Claude Code before `apply` changes MCP servers: it rewrites `~/.claude.json` while it runs.

| Message | Fix |
|---|---|
| `ERROR another aicfg apply is running (lock: <path>)` | Another `apply` (or `update`) holds `$AICFG_HOME/apply.lock`. Let it finish, then re-run. The lock is released when that process exits, even if it crashed, so there is nothing to delete. |
| `CHANGED <harness> <file>  (changed during apply; close Claude Code and re-run)` | The file changed after `apply` read it, so `apply` left it alone and exited 1. Close the harness that writes it, then re-run. |

## Uninstall

1. Disable every harness in `harnesses.local.toml`, and every pack in `packs.local.toml`:

   ```toml
   [claude]
   enabled = false
   ```

   Repeat for `codex`, `opencode`, `antigravity`, and `cursor`.
2. Run `python3 scripts/aicfg.py apply`. It removes every link it made, including the hooks
   directory, takes ai-config's hooks out of `~/.claude/settings.json`, and removes the MCP
   servers it added (backing each file up first). Your other settings, hooks, and servers stay.
3. Delete the repo.

## A guard hook blocked something safe, or missed something risky

The Claude Code hooks match command patterns ([guardrails.md](guardrails.md)), so both happen.
Open an issue with the exact command or tool call, what the hook did, and what you expected.
A fix comes with two tests in `tests/test_hooks.py`: the risky command, and a safe near-miss
that must still pass (for example `git push origin x` asks, `git log` doesn't).
