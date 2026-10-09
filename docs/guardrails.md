# Guardrails

Layered, so no single layer has to be perfect.

| Layer | Where | Enforced by | Covers |
|---|---|---|---|
| Rules | `rules/30-guardrails.md`, `40-security.md` | model instructions, every tool | approvals, untrusted input, secrets |
| Workflow | `skills/spec-agent/references/guardrails.md` | engine | gates, stop conditions, retry budget, scope fence, environment targets |
| Role scoping | `agents/*.md` `tools:` | Claude Code / OpenCode | reviewers and planners can't edit code |
| Hooks | `overrides/claude/hooks/` | Claude Code harness | prompts/blocks regardless of what the model decides |
| Repo | `.pre-commit-config.yaml`, CI | git / GitHub | gitleaks, validation, no home paths |

## Claude Code hooks

**`guard_outward.py`** (Bash and `mcp__*` tools) → asks for confirmation before:
- git push, `reset --hard`, `clean -f`, `branch -D`, including with global options
  (`git -C dir push`); `gh` writes (PRs, issues, releases, repo, secrets, workflow runs,
  `gh api` writes, GraphQL mutations)
- MCP tools whose name contains a write verb (`create_pull_request`, `addCommentToJiraIssue`,
  `slack_send_message`, …), except local-only servers (memory, sequential-thinking, context7)
- package/image publishing, `docker login`
- `terraform|tofu|terragrunt` apply/destroy/import/taint/force-unlock, state surgery, workspace delete
- `kubectl` mutations (apply, delete, patch, scale, exec, rollout restart, …), `helm`
  install/upgrade/uninstall/rollback: **dry runs pass through**
- `argocd app sync|delete|rollback|…`, `flux reconcile|suspend|…`
- AWS CLI writes (create/delete/put/update/terminate/invoke/…, `s3 cp|mv|rm|sync`) and secret reads
  (`secretsmanager get-secret-value`, `ssm get-parameter --with-decryption`)
- migration tools and `psql` writes against **non-local** databases
- Proxmox `qm`/`pct` destroy/stop/…, `talosctl` upgrade/reset/…, host reboot/poweroff
- `rm -rf` in any flag spelling

Commands inside `sh -c '…'`, `eval`, `$(…)`, and backticks are unwrapped and checked, and shell
operators are split even without spaces (`ls;kubectl delete …`). Read-only and offline commands
(plan, validate, template, lint, diff, get, describe) are not prompted; `--dry-run=none` counts
as a real run.

**`guard_secrets.py`** (Read/Write/Edit/MultiEdit/Grep/Bash):
- deny writing credential-shaped content (AWS key IDs and secret keys, GitHub, GitLab,
  Anthropic/OpenAI, Slack, Google, Stripe keys, JWTs, private keys); the matched value is never echoed
- deny writing secret files: `.env*` (except `.example`/`.sample`/`.template`/`.dist`), `.envrc`,
  `.netrc`, `.aws/credentials`, `.docker/config.json`, `.kube/config`, `.pgpass`, `.npmrc`, `.pypirc`
- ask before reading or grepping them, including Bash commands that name one (`cat .env`,
  `--env-file=.env`)

Both are stdlib Python, tested in `tests/test_hooks.py`. The hooks are pattern-based: they catch
accidents and skipped gates, not a determined adversary. Known gaps: shell aliases (`k`, `tf`),
scripts that run mutations internally, and MCP tools whose names carry no verb (e.g. `batch`).
Harness permission modes still apply.

## Gaps by tool

OpenCode runs the same guards through a plugin (`overrides/opencode/plugin.js`), with one
difference: a plugin can't prompt, so anything the guards would ask about is blocked, and the
model is told to ask you to run it yourself. MCP tools aren't guarded there yet.

Codex, Antigravity CLI, and Cursor get the rules and workflow layers only. Use their own
permission/sandbox settings (e.g. Codex approval modes) alongside. Porting the hooks to tools
that support pre-execution hooks is on the [roadmap](roadmap.md).
