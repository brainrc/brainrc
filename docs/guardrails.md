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

**`guard_outward.py`** (Bash) → asks for confirmation before:
- git push, `reset --hard`, `clean -f`, `branch -D`; `gh` writes (PRs, issues, releases, repo,
  secrets, workflow runs, `gh api` writes)
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

Read-only and offline commands (plan, validate, template, lint, diff, get, describe) are not prompted.

**`guard_secrets.py`** (Read/Write/Edit/MultiEdit):
- deny writing credential-shaped content (AWS, GitHub, Anthropic/OpenAI, Slack, Google, Stripe keys,
  private keys); the matched value is never echoed
- deny writing `.env*` (except `.example`/`.sample`/`.template`); ask before reading them

Both are stdlib Python, tested in `tests/test_hooks.py`. The hooks are pattern-based: they catch
accidents and skipped gates, not a determined adversary. Harness permission modes still apply.

## Gaps by tool

Codex, Gemini CLI, OpenCode, and Cursor get the rules and workflow layers only. Use their own
permission/sandbox settings (e.g. Codex approval modes) alongside. Porting the hooks to tools
that support pre-execution hooks is on the [roadmap](roadmap.md).
