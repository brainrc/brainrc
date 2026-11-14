# Guardrails

Layered, so no single layer has to be perfect.

| Layer | Where | Enforced by | Covers |
|---|---|---|---|
| Rules | `rules/30-guardrails.md`, `40-security.md` | model instructions, every tool | approvals, untrusted input, secrets |
| Workflow | Gatework's `skills/brainrc-gatework/references/guardrails.md` | engine | gates, stop conditions, retry budget, scope fence, environment targets |
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
- host reboot/poweroff. Proxmox `qm`/`pct` and `talosctl` are in the [homelab example pack](../examples/pack-homelab/README.md).
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

**`check_mcp_pins.py`** (SessionStart, on startup and resume) → warns when an MCP server's tools changed
after you approved them, the "rug pull" case. `brainrc pin-mcp` starts each stdio server brainrc
installs for Claude Code, lists its tools, shows what changed, and on your yes records a hash of
each tool definition in `$BRAINRC_HOME/mcp-pins.json`. At session start the hook lists the
pinned servers' tools again and, for any tool changed, added or removed, shows a warning and
tells the model not to call those tools until you re-run `pin-mcp`. It fails open: no pins, a
server that won't start, or one that doesn't answer within 4 seconds (all servers in parallel)
warns nothing, but a server left unchecked three sessions running is named to you. Each run
writes its duration to `mcp-pins.last.json`. Tool names reach the model only when they are plain
identifiers. Servers start in your home directory for both `pin-mcp` and the hook, so a check
doesn't depend on the project. HTTP servers aren't pinned, since brainrc has no network code;
`apply` names every stdio server whose tools aren't pinned and drops the pins of servers it no
longer installs. The hook starts its own copy of each pinned server next to Claude Code's.

All three are stdlib Python, tested in `tests/test_hooks.py` and `tests/test_mcp_pins.py`.
Harness permission modes still apply.

## Known gaps

The hooks match command text. They catch accidents and skipped gates, not a model (or a
prompt-injected ticket) set on getting around them. Matching text can't close these gaps:

- **Aliases and wrappers**: `k delete …`, `tf apply`, a `Makefile` target, a shell function.
- **Indirect execution**: a script, test, or build step that mutates internally
  (`python deploy.py`, `go run ./cmd/migrate`, a `boto3` or Kubernetes client call).
- **MCP tools with no verb in the name** (`batch`, `run`, `execute`), and MCP servers that
  are themselves write-capable.
- **Credentials already in the environment**: if the shell has an admin AWS profile, a kube
  context with cluster-admin, or a Terraform backend it can write, one missed pattern is
  enough to change real infrastructure.

So the hooks are a seatbelt. What stops a write is the **credentials**: a run should hold none
that can apply, mutate a cluster, or write to a cloud account.

### Recommended setup for runs that touch infrastructure

1. **Read-only credentials by default.** spec-agent's live evidence (plan, diff, describe) needs
   reads only (`targets` in `state.json`). Give runs credentials that can do nothing else:
   - AWS: a dedicated profile that assumes a role with `ReadOnlyAccess` (or a narrower
     `ViewOnlyAccess` plus the specific reads you need). Export only that
     `AWS_PROFILE`; keep admin profiles out of the run's shell and `~/.aws/config` if you can.
   - Kubernetes: a kube context whose user is bound to the built-in `view` ClusterRole, in a
     separate kubeconfig (`KUBECONFIG=~/.kube/ai-readonly`). `view` can't read Secrets.
   - Terraform/Terragrunt: plan with the read-only role and `-lock=false`, against a backend
     the role can read but not write. Applies happen in CI (Atlantis, Spacelift, a pipeline)
     after merge, with credentials the agent never sees.
   - GitHub: a fine-grained token limited to the repos in play, without admin or
     workflow-write scope. Deliver needs only contents and pull-request write.
2. **Sandbox the run.** Run the harness in a devcontainer, VM, or the harness's own sandbox
   (Claude Code's sandboxed Bash, Codex `workspace-write` sandbox mode), with only the
   read-only credentials mounted and network egress limited to what the run needs.
3. **Keep write paths out of reach.** Production kube contexts, state buckets, and break-glass
   roles should not exist on the machine the agent runs on. If they must, use a separate OS
   user or profile for agent sessions.
4. **Hooks still on.** They catch the honest mistakes early and prompt before outward actions,
   which keeps the Deliver gate meaningful.

With this setup, a bypassed hook produces an access-denied error rather than a change.

## Gaps by tool

OpenCode runs the same guards through a plugin (`overrides/opencode/plugin.js`), with one
difference: a plugin can't prompt, so anything the guards would ask about is blocked, and the
model is told to ask you to run it yourself. MCP tools aren't guarded there yet.

Cursor runs them through `overrides/cursor/hooks/guard.py` on `beforeShellExecution` (both
guards) and `beforeReadFile` (secrets), from `~/.cursor/hooks.json` (`brainrc`) or the plugin's
`.cursor-plugin/hooks.json`. Cursor's `ask` was reported broken and reads accept only allow or
deny, so ask becomes deny there too. File writes and MCP calls aren't guarded in Cursor: it has no
reliable pre-write hook. Not yet run in a real Cursor.

Codex and Antigravity CLI get the rules and workflow layers only. Use their own
permission/sandbox settings (e.g. Codex approval modes) alongside. Porting the hooks to tools
that support pre-execution hooks is on the [roadmap](roadmap.md).
