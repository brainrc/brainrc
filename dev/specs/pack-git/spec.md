# Spec: packs from a git URL, fetched by aicfg

Ticket: gh:50 (refs) · Size: standard (config key, fetch, update command, doctor, docs) · Status: approved

## Acceptance criteria
- **AC1** A pack entry may use `git = "<url>"` with an optional `ref` (tag, branch, or commit)
  instead of `path`; one of the two is required, not both. Its clone lives in
  `$AICFG_HOME/packs/<key>` (outside any checkout or package).
- **AC2** `apply` fetches a missing git pack before planning: a shallow fetch of `ref` (or the
  remote's default branch) checked out detached. It prints `FETCH <key> <url> (<ref>)`. A failed
  fetch is an ERROR: nothing is written, exit 1. An existing clone is used as is, so `apply`
  needs no network once fetched. `status` writes nothing: it prints the FETCH it would do and
  plans without that pack.
- **AC3** New command `aicfg update`: refetch every enabled git pack at its `ref`, then apply.
  A clone with local changes is left alone with an ERROR, and nothing is written.
- **AC4** `doctor`: a git pack that isn't fetched is a FAIL (fix: apply). Its `requires_core`
  and validate checks work as for path packs. `validate --pack` still takes a directory.
- **AC5** Tests use a local bare repo (`file://`), offline: first apply clones it and links its
  skills; `status` doesn't fetch; `update` moves to a new tag; a bad URL is an ERROR with
  nothing written; dirty clone; `path` + `git` together is an error; doctor finding. Real run
  in a fake HOME with the installed `aicfg` (uv) and the example pack served from a bare repo.
- **AC6** Docs: `docs/packs.md` (git packs, update, private repos use your git credentials),
  `packs.toml` comments, README, `docs/harness-packages.md`; CHANGELOG; VERSION 0.3.23 (PATCH:
  new optional key, `path` unchanged).

## Not in this step
Claude plugin `dependencies` (Claude-only), signature checks, removing clones of packs dropped
from config (left on disk), and doctor warnings for clones behind their remote.

## Open choice
**How a pack installs without a hand clone:**
- (A, recommended) aicfg fetches it with git. This works for every harness and for private
  repos, using your git credentials.
- (B) Claude Code plugin `dependencies`. Only Claude Code installs it, and other harnesses still
  need a path.
