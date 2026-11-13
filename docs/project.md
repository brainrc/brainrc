# Project manifest and lockfile

A team commits two files to its repo: `brainrc.toml`, which says which packs the repo's agents
use, and `brainrc.lock`, which records exactly what those packs were when `apply` last ran. Every
machine and CI job then produces the same agent files from the same lock.

This page is the contract for both files. It is language-neutral: another implementation that
reads and writes them as described here is compatible. The JSON Schemas
[`schemas/brainrc.toml.schema.json`](schemas/brainrc.toml.schema.json) and
[`schemas/brainrc.lock.schema.json`](schemas/brainrc.lock.schema.json) describe each file after
it is parsed as TOML; `brainrc` checks both files against them on every read. Conformance
fixtures are in `tests/fixtures/lockfile/`.

## Scopes

- **User scope** is what `brainrc` has always done: packs from `packs.toml` and
  `packs.local.toml`, linked into each installed harness's home. Its lock is
  `$BRAINRC_HOME/brainrc.lock` (default `~/.config/brainrc/brainrc.lock`).
- **Project scope** is a repo with `brainrc.toml` at its root. Its agent files are written into
  the repo, and its lock is `brainrc.lock` next to `brainrc.toml`. `brainrc` finds the project
  from the current directory: that directory or a parent, up to the repo root (the first
  directory that holds `.git`).

Both scopes apply together. The user's own config still layers on top of a project's at run
time, because harnesses read the user's home and the repo.

## What `apply` writes in a project

`brainrc apply` (and `status`, which writes nothing) runs the user scope first, then the project
in the current directory, under its own `Project <dir> (brainrc.toml)` heading.

- **Skills** are copied, not linked, to `.agents/skills/<name>/`, so the repo works on every
  machine and in CI. A link inside a skill (Gatework's `roles/`) is copied as the files it points to.
- **Rules** from the project's packs go into a marked block in `AGENTS.md`:
  `<!-- brainrc:begin: … -->` to `<!-- brainrc:end -->`. Your own text above and below the block
  stays. With no rules, there is no block, and a file that held only the block is removed.
- **Only the project's packs**: core's rules and guard hooks, MCP servers and anything
  machine-local (`packs.local.toml`, `brainrc.local.toml`, `*.local.md`) stay in the user scope,
  so they never change a project's files.
- **Git packs** are fetched by `apply`, never by `status`, into
  `$BRAINRC_HOME/project-packs/<key>-<id>`, one clone per URL and ref.
- **Ownership**: `brainrc.lock` lists every file `brainrc` wrote (`outputs`). A file there is
  updated or removed as its pack changes. A file brainrc didn't write, or one you changed after
  it was removed from the packs, is a `CONFLICT` and is left alone.

## Moved tags and branches

`apply` resolves each git pack's `ref` and records the commit; `update` refetches every ref. When
a ref the lock already has now resolves to another commit (a tag was moved, a branch moved on),
`apply` and `update` print `MOVED <pack> <ref>: <old> -> <new>` and relock it. `status` never
fetches, so it reports a move only once this machine's clone has the new commit; it then names
both commits and writes nothing.

## Installing from the lock

`brainrc install --frozen` installs exactly what `brainrc.lock` records, for CI and teammates. It
fetches each git pack's locked `commit`, never its `ref`, so a moved tag changes nothing. Every
check runs before anything is written: the packs in `brainrc.toml` (or `packs.toml`) and the lock
must match by key, URL, ref and path, and every file must hash as the lock says, outputs included.
On any mismatch it names each one, writes nothing and exits 1. It never rewrites the lock and
never removes files. It won't overwrite a file brainrc didn't write either: one at a locked path
whose hash is neither the lock's nor what brainrc last wrote there on this machine (kept in
`$BRAINRC_HOME/project-state/`), or a hand-edited block in `AGENTS.md`. It names each one and
writes nothing; `--force` overwrites them. The scope is the project when there is a `brainrc.toml` here or above, else
the user; `--scope user|project` picks one. `brainrc install` without `--frozen` is `apply`.

## `brainrc.toml`

```toml
version = 1                                  # optional; 1 is the only version
exclude = ["gatework:skills/brainrc-aws"]    # optional; items to leave out (see below)
harnesses = ["claude", "codex"]              # optional; tools that get their own files

[packs.gatework]        # a default pack: on unless `enabled = false`
ref = "v0.7.1"          # pin it to another ref; its `git` URL is kept

[packs.acme]
git = "https://example.com/acme/agent-pack.git"
ref = "v2"

[packs.team]
path = "tools/agent-pack"   # relative to the repo root
```

| Key | Type | Meaning |
|---|---|---|
| `version` | integer | Format version. `1`, the default. |
| `exclude` | array of strings | Items not to install, as a path in the pack (`skills/brainrc-aws`) or after its name (`gatework:skills/brainrc-aws`); `*` and `?` match. |
| `harnesses` | array of strings | Harnesses (from `harnesses.toml`) that get tool-specific files besides the standard ones. Default: every harness in core's `harnesses.toml`. |
| `packs.<key>` | table | One pack. `<key>` is lowercase letters, digits and `-`. |
| `packs.<key>.enabled` | boolean | Default `true`. `false` turns a default pack off. |
| `packs.<key>.git` | string | A URL to fetch. Can't start with `-`. |
| `packs.<key>.ref` | string | With `git`: tag, branch or commit. Default: the remote's default branch. |
| `packs.<key>.path` | string | A directory inside the repo, relative to the repo root, using `/`. No `..`, `~`, `$` or leading `/`. |
| `packs.<key>.description` | string | A note for people; ignored. |

- **Default packs** are the tables in core's `packs.toml` (Gatework). They are on in every
  project unless `brainrc.toml` sets `enabled = false`. A `ref` alone keeps the default pack's URL;
  `git` or `path` replaces its origin.
- Any other pack needs exactly one of `git` and `path`.
- Unknown keys are errors, so a typo never silently changes what is installed.

## `brainrc.lock`

`apply` writes it; nobody edits it. A second `apply` with no change to any source leaves it
byte-identical.

```toml
# brainrc.lock: written by brainrc. Don't edit it by hand.
version = 1
brainrc = "0.7.3"
scope = "project"

[packs.gatework]
git = "https://github.com/brainrc/gatework.git"
ref = "v0.7.1"
commit = "753b9960c5e0d2f1a4b7c8e9d0a1b2c3d4e5f607"

[packs.gatework.files]
"agents/brainrc-analyst.md" = "sha256:3f1c…"
"skills/brainrc-work/SKILL.md" = "sha256:9a0b…"

[packs.team]
path = "tools/agent-pack"

[packs.team.files]
"skills/team-deploy/SKILL.md" = "sha256:5d2e…"

[outputs]
".agents/skills/brainrc-work/SKILL.md" = "sha256:9a0b…"

[blocks]
"AGENTS.md" = "sha256:77c4…"
```

| Key | Type | Meaning |
|---|---|---|
| `version` | integer | Format version, `1`. A reader refuses a version it doesn't know. |
| `brainrc` | string | The brainrc version that wrote it, `MAJOR.MINOR.PATCH`. |
| `scope` | string | `user` or `project`. |
| `packs.<key>` | table | Every enabled pack, and nothing for a disabled one. |
| `packs.<key>.git` | string | The URL fetched, with any user name or password removed. |
| `packs.<key>.ref` | string | The ref asked for (`HEAD` when the config names none). |
| `packs.<key>.commit` | string | The commit that ref resolved to: 40 or 64 lowercase hex digits. Git packs only. |
| `packs.<key>.path` | string | A path pack's directory as the config wrote it; under the home directory it is written with `~`. Path packs have no `commit`. |
| `packs.<key>.files` | table | Every installed file of the pack (below): its path in the pack, using `/`, to its hash. |
| `outputs` | table | Project scope: every file `brainrc` wrote into the repo, repo-relative, to its hash. |
| `blocks` | table | Project scope: files `brainrc` shares with you (`AGENTS.md`): the hash of its marked block. |

A hash is `sha256:` and 64 lowercase hex digits, the SHA-256 of the file's bytes. A pack has
exactly one of `git` (with `commit`) and `path`. `outputs` and `blocks` appear only in a
project lock, and only when they have entries; empty `files` tables are written too.

**A pack's installed files** are the files `brainrc` reads from it to install: `pack.toml`, the
file its `validator` names, `rules/*.md` (not `README.md` or `*.local.md`), each item it installs
(every file under `skills/<name>/`, `agents/<name>.md`, `commands/<name>.md`) after the profile
and `exclude` are applied, and, in user scope with hooks installed, every file under
`overrides/`. Symbolic links are followed, so a file is hashed as it is read. `__pycache__`
directories are skipped.

**Determinism.** The lock is UTF-8 with `\n` line endings and ends with one newline. The first
line is the comment above. Then come `version`, `brainrc` and `scope`, in that order. Then one
`[packs.<key>]` table per pack sorted by key, its keys in the order `git`, `ref`, `commit`, or
`path`, each followed by its `[packs.<key>.files]` table. Then `[outputs]` and `[blocks]`. Every
table's entries are sorted by key (by Unicode code point). Keys that aren't bare keys
(`A-Za-z0-9_-`) are written as basic strings. Strings escape `"`, `\` and control characters as
TOML basic strings do. The lock holds no timestamps, no host or user names, no credentials and
no absolute path to the home directory.

**Ready for more.** Future keys (pinned commands, permission records) are added inside
`packs.<key>` or as new top-level tables, with a `version` bump only for a change an old reader
would misread.
