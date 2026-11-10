Write brainrc on-disk names and converge the old ones

## Why
`apply` still wrote three ai-config names to users' machines: the Codex MCP block markers, the OpenCode guard link
and the git pack fetch record. Renaming them blindly would make apply treat its own old output as foreign. You
would get a second Codex block, a second OpenCode guard, or a needless re-fetch.

## What changed
- Codex: the block markers are now `# >>> brainrc mcp servers ...` / `# <<< brainrc mcp servers`. Old-marker
  blocks are recognized, and the first block is rewritten in place, so the user's bytes around it don't change.
  A block with no end marker is left alone, and its servers show as CONFLICT.
- OpenCode: the guard link is `~/.config/opencode/plugins/brainrc-guard.js`. The old `ai-config-guard.js` is
  pruned only when it is a symlink to the managed guard.
- Git packs: the fetch record is `.git/brainrc-fetched.json`. The old `.git/aicfg-fetched.json` still counts,
  so there is no re-fetch. Apply writes the new record and removes the old one. `status` writes nothing.

## Acceptance criteria
- [x] AC1: an old Codex block converges to one brainrc block, in place, and the next apply changes nothing
- [x] AC2: new configs get the brainrc markers; an old block and a new block together leave one
- [x] AC3: the old guard link is replaced; a real file or a foreign symlink is left alone; status is in sync
- [x] AC4: the old record is read, then replaced on apply; a mismatching old record still triggers a fetch
- [x] AC5: the allowlist rows are narrow; the suite passes with and without `XDG_CONFIG_HOME`

## How to verify
```
python3 -m unittest discover -s tests
XDG_CONFIG_HOME=/home/runner/.config python3 -m unittest discover -s tests
python3 scripts/brainrc.py validate
```

## Decisions made without you
- Apply removes the old fetch record once the new one is written.
- Apply keeps recognizing the old names after 0.5.0. This is on-disk convergence, not a name users type.
- The Codex block is now replaced where it sits, instead of being moved to the end of the file. Files written by
  earlier versions already have it at the end, so they don't change.
- Local ticket `specs/tickets/237-rename-on-disk-names.md` (there is no GitHub issue).

## Follow-ups
- none

Spec: `specs/237-rename-on-disk-names/spec.md`
