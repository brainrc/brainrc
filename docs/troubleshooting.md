# Troubleshooting

Start here: this lists what's wrong with the install on this machine and how to fix each item.
It changes nothing.

```bash
python3 scripts/brainrc.py doctor
```

Then find the symptom below.

## A harness doesn't see a skill, agent, command, or rule

Run `python3 scripts/brainrc.py apply`. Skills, agents, and commands are symlinks, so edits to
existing ones show up at once, but new or removed ones need `apply`. Rules are different:
they're rendered into `~/.config/brainrc/instructions.md` (or `$BRAINRC_HOME`), so **every** change to `rules/` (or a pack's
rules) needs `apply`, edits included. Restart the harness or start a new session afterwards.

If you moved the repo, the old links are broken and `apply` reports each as a `CONFLICT`. Run
`python3 scripts/brainrc.py apply --repair` from the new location: it relinks every broken link
that points at the same item's old location (`skills/<name>`, `agents/<name>.md`, ...) and prunes
the ones whose item is gone. `status --repair` shows the changes first. A broken link to anything
else stays a `CONFLICT`.

## Every skill shows up twice, or a hook runs twice

Both the Claude Code plugin and the `brainrc` command's links are installed. Keep one: `/plugin uninstall
brainrc@brainrc`, or remove the links (below).

If `doctor` warns that the old plugin `ai-config@ai-config` is installed, you have the plugin
under both names: follow [Moving from ai-config](install.md#moving-from-ai-config).

## `CONFLICT` in `status` or `apply`

A real file, or a symlink pointing outside this repo and your packs, sits where `brainrc` wants
a link. `brainrc` never overwrites it. Look at it, then either:

- move it into the repo or a pack (as a skill, agent, or command) and delete the original, or
- delete it if you don't need it,

and run `apply` again. `CONFLICT` on a settings file means it isn't valid JSON: fix it by
hand. `CONFLICT` naming an MCP server means your harness config already defines a server of that
name: rename or remove yours (or the registry's), then run `apply`.

## Config errors

`status`, `apply`, `validate`, and `doctor` check `harnesses.toml`, `packs.toml`, their
`.local.toml` overrides, and each pack's `pack.toml` first, and name the file and line:

| Message | Fix |
|---|---|
| `ERROR harnesses.local.toml:3: invalid TOML: Invalid value` | Fix the TOML on that line (often a missing value or quote). |
| ``ERROR harnesses.local.toml:2: `claude` must be a table, e.g. [claude]`` | Write `[claude]` on its own line, then `enabled = false` under it. |
| ``ERROR harnesses.local.toml:3: [codex] `enabled` must be true or false`` | Use `true` or `false` without quotes. Paths and `ref` must be quoted strings. |
| ``WARN harnesses.local.toml:2: unknown key `enabeld` in [claude]`` | A typo: the key is ignored until you fix it. |
| `WARN harnesses.local.toml:4: unknown harness [cursr]` | A typo, or a harness `harnesses.toml` doesn't list. It still loads. |

Errors stop the command before it writes anything; warnings don't.

## Pack errors

| Message | Fix |
|---|---|
| ``pack name `acme` is used by both [work] and [acme]`` | Two packs share one `name`. Change `name` in one `pack.toml`, or set `enabled = false` for one in `packs.local.toml`. `core` is taken. |
| ``skill `acme-deploy` is defined in both acme and acme2`` | Rename one. Each pack's items carry its own `prefix`. |
| ``acme:skills/x: pack skills must start with `acme-` `` | Rename the item to start with the pack's `prefix`. |
| ``acme:pack.toml: `prefix` must be lowercase-hyphenated and end with '-'`` | Fix `prefix` in `pack.toml`, e.g. `acme-`. |
| ``acme:pack.toml: requires_core `>=2.0` is not satisfied by core 1.2.3`` | Update core (`git pull`) or the pack, or set `enabled = false` for it in `packs.local.toml`. |
| `pack acme: no pack.toml at ...` | Fix the pack's `path` in `packs.local.toml`. |

`validate` reports all of these. `apply` and `status` check each pack the same way first and
write nothing while any of them stands, naming `validate --pack <dir>` for the pack to fix. See [packs.md](packs.md).

## Settings backups

Before `apply` changes a harness's settings file (Claude Code: `~/.claude/settings.json`), it
copies it next to the original as `settings.json.bak-brainrc-<UTC time>`. The last 5 are kept, counting
old `settings.json.bak-aicfg-<UTC time>` backups too.
No backup is made when the file didn't exist yet. MCP config files (`~/.claude.json` and the
others) are backed up the same way.

The rewritten file and its backup keep the original's permissions, so a `0600` `~/.claude.json`
stays `0600`. If the path is a symlink (a dotfiles-managed `settings.json`), `apply` writes
through to the link's target and leaves the link in place; the backup goes next to the target.

## Apply while something else writes

Close Claude Code before `apply` changes MCP servers: it rewrites `~/.claude.json` while it runs.

| Message | Fix |
|---|---|
| `ERROR another brainrc apply is running (lock: <path>)` | Another `apply` (or `update`) holds `$BRAINRC_HOME/apply.lock`. Let it finish, then re-run. The lock is released when that process exits, even if it crashed, so there is nothing to delete. |
| `CHANGED <harness> <file>  (changed during apply; close Claude Code and re-run)` | The file changed after `apply` read it, so `apply` left it alone and exited 1. Close the harness that writes it, then re-run. |

## Uninstall

```bash
python3 scripts/brainrc.py uninstall --dry-run   # see what goes
python3 scripts/brainrc.py uninstall             # or `brainrc uninstall` from the package
```

`uninstall` removes every link brainrc made (broken ones too), takes its hooks out of each
settings file and the MCP servers it added out of each MCP file, and removes the files and
directories that leaves empty. Your own settings, hooks, and servers stay, every file it
rewrites is backed up first (`*.bak-brainrc-*`), and an instructions file `init` moved aside is
put back. It reads which harnesses and source roots apply used from `$BRAINRC_HOME/harnesses.json`,
so it still works after you move or delete the checkout or a pack.

Your local config (`harnesses.local.toml`, `packs.local.toml`, `rules/*.local.md`) and fetched
git packs stay in `$BRAINRC_HOME`; `uninstall --purge` deletes that directory too, unless it
holds files brainrc didn't make (then it says which, and leaves them). Then delete
the repo, or `uv tool uninstall brainrc` (`pipx uninstall brainrc`).

## Every tool call is blocked, or `doctor` says `hook missing`

In older installs, a hook whose script had gone (checkout moved or deleted, package removed, Python
upgraded) exited 2, which Claude Code treats as a block on every tool call. Run `apply` to
rewrite the hook commands: they now skip a missing script (Cursor's reply "allow"), so the
harness keeps working. That also means the guard is off until it's fixed, so `doctor` checks
each one:

| Finding | Fix |
|---|---|
| `<harness>: hook missing: <path>` | Run `apply` from the checkout or install you use now; it re-links the hooks dir. |
| `<harness>: hook <path> exits <n> on an empty payload` | Run `python3 <path>` and read the error (often a Python too old for the guard), then `apply`. |
| `<harness>: hook <path> timed out after <n>s` | Run it by hand to see where it hangs. |
| `<harness>: hook <path> can't run: python3 is not on PATH` | Install Python 3, or put `python3` on the PATH the harness starts with. |

## A guard hook blocked something safe, or missed something risky

The Claude Code hooks match command patterns ([guardrails.md](guardrails.md)), so both happen.
Open an issue with the exact command or tool call, what the hook did, and what you expected.
A fix comes with two tests in `tests/test_hooks.py`: the risky command, and a safe near-miss
that must still pass (for example `git push origin x` asks, `git log` doesn't).
