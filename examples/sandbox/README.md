# Sandbox

A tiny stdlib-only Python CLI for trying spec-agent end to end without risk.
Copy it out of this repo first so the workflow's branches and commits land in a throwaway repo:

```bash
cp -R examples/sandbox /tmp/spec-sandbox && cd /tmp/spec-sandbox
git init -q -b main && git add -A && git commit -qm "Initial sandbox"
python3 -m unittest -q
```

Then, in your AI tool, from `/tmp/spec-sandbox`:

| Ticket | Tests |
|---|---|
| `/work local:tickets/001-add-shout-flag.md` | happy path: spec and plan gates, TDD task, verify, deliver drafts |
| `/work local:tickets/002-injection-check.md` | untrusted-content handling: the embedded instructions must be ignored and flagged |

There is no remote, so Deliver skips the PR and records the branch (see the ticket-local skill).
Check `specs/<slug>/` afterwards: `state.json`, `log.md`, `verify.md`, and `retro.md`.
