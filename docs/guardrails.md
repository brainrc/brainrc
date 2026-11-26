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

A pack adds its own deny and ask rules in `pack.toml`, under its `[scope]`, and this hook enforces
them with the same unwrapping; a pack's deny wins over any ask ([guard rules](packs.md#guard-rules)).

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

## Auditing what agents load

`brainrc audit` lists, per harness, every skill, agent, command, rule, hook and MCP server brainrc
puts there: the pack it came from, that pack's commit, the item's sha256 (a directory's is the hash
of its files' paths and hashes), and whether it's installed now. Then come each pack's permissions
from `brainrc.lock` and each MCP server's tool pins. `--json` prints the same for a security
review or a script. It reads only (no network, nothing written); paths under ~ are written with ~,
URLs lose any user name, password, query and fragment, the value after a token, key, secret,
password or auth flag in a server's arguments is shown as `…`, and server environments are named,
never read. A rule counts as installed once the rendered instructions hold it, and an MCP server
once brainrc's own record says it wrote it.

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

A pack's `path` and `host` [guard rules](packs.md#guard-rules) close part of this for Claude Code:
they compile into its OS sandbox, which refuses the read, write or connection whatever program
makes it, once `sandbox.enabled` is on. The sandbox covers Bash and what it starts, not the Read
tool or web fetches, which follow permission rules.

So the hooks are a seatbelt. What stops a write is the **credentials**: a run should hold none
that can apply, mutate a cluster, or write to a cloud account.

### Recommended setup for runs that touch infrastructure

1. **Read-only credentials by default.** Gatework's live evidence (plan, diff, describe) needs
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
model is told to ask you to run it yourself. A pack's [guard rules](packs.md#guard-rules) apply
under its `[scope]`, judged from the bash tool's `workdir`, else the session's directory, and a
pack's deny reads as a refusal. MCP tools get the outward guard too: OpenCode names them
`<server>_<tool>`, so the plugin asks OpenCode which servers are connected and matches the longest,
and the guard reads the call as `mcp__<server>__<tool>`. Run in a real OpenCode (1.19.6). A pack can ship its own
OpenCode plugin as `overrides/opencode/plugin.js`; `apply` links it beside core's, and the lock
records it with the pack's hooks ([packs](packs.md#layout)).

Cursor runs them through `overrides/cursor/hooks/guard.py` on `beforeShellExecution` (both
guards) and `beforeReadFile` (secrets), from `~/.cursor/hooks.json` (`brainrc`) or the plugin's
`.cursor-plugin/hooks.json`. Cursor's `ask` was reported broken and reads accept only allow or
deny, so ask becomes deny there too. A pack's [guard rules](packs.md#guard-rules) apply under its
`[scope]`, judged from the event's `cwd` (else the first workspace root), and a pack's deny reads as
a refusal, not as a call to ask you. File writes and MCP calls aren't guarded in Cursor: it has no
reliable pre-write hook. Not yet run in a real Cursor: it is tested with payloads shaped like the
hook input in the [`cursor-hooks`](https://www.npmjs.com/package/cursor-hooks) types.

Codex runs them through `overrides/codex/hooks/guard.py` on `PreToolUse`, from
`$CODEX_HOME/hooks.json`: shell commands get both guards, MCP tools the outward guard, and
`apply_patch` the secrets guard (each file it adds or changes, with its added lines). Codex's
`PreToolUse` takes only allow and deny, and treats an ask as a failed hook that lets the call run,
so ask becomes deny there too. A pack's guard rules apply under its `[scope]`, judged from the
payload's `cwd`; Codex names an MCP server's tools with its `-` turned into `_`, and a rule matches
either spelling. Codex runs a hook only after you trust it: open `/hooks` in Codex once after
`brainrc apply`. Until then it skips the hooks without a word, `codex exec` included. Hosted tools
such as web search don't reach the hook. Run in a real Codex (0.172), shell, `apply_patch`, code
mode and MCP calls alike.

Antigravity runs them through `overrides/antigravity/hooks/guard.py` on `PreToolUse` for
`run_command`, from `~/.gemini/config/hooks.json`, where brainrc's hooks sit under their own entry,
`brainrc`. A guard's ask replies `force_ask`, which prompts even for a command you allowed before,
and a deny replies `deny`. With no objection it replies `allow`, which Antigravity's docs define as
handing the call on to the next hook or the default policy, so your own permission settings still
decide; it is not `auto_approve`. In headless `agy -p`, which can't prompt, an ask ends as a deny. A
pack's guard rules apply under its `[scope]`, judged from the command's `Cwd`, else the first
workspace path. File tools and MCP tools aren't guarded there yet: the docs don't name their
arguments or how MCP tools are called. Not yet run in a real Antigravity: it is tested with payloads
shaped like the docs' `run_command` example.

Five more tools run them through their own `overrides/<tool>/hooks/guard.py`, each turning its
tool's call into Claude Code's (#307 to #312). None has been run in the live tool yet: each is
tested with payloads shaped like its docs, and where the docs don't name a tool's arguments the
guard reads the likely fields and lets anything else through.

- **GitHub Copilot** (`~/.copilot/hooks/brainrc.json`, `preToolUse`): shell (`bash`, `powershell`)
  gets both guards, `view` reads and `create` or `edit` writes the secrets guard. It replies
  `permissionDecision: deny`; Copilot acts on no ask, so ask becomes deny. MCP calls aren't
  guarded: the docs don't say how Copilot names them.
- **Devin Local** (`~/.config/devin/config.json`, `PreToolUse`): `exec`, `read`, `write`, `edit`
  and `mcp__<server>__<tool>`. It replies `decision: block`, so ask becomes a block. Its payload
  has no working directory, so a pack's `[scope]` is judged from `$DEVIN_PROJECT_DIR`.
- **Kiro** (`~/.kiro/hooks/brainrc.json`, `PreToolUse` on every tool): `execute_bash`, `fs_read`,
  `fs_write`, `str_replace` and `mcp_<server>_<tool>`. A command hook blocks by exiting non-zero
  with the reason on stderr, so ask becomes a block, and the guard exits 0 for anything it can't
  read: a crash would block the call. Kiro CLI loads `~/.kiro/hooks` as global hooks.
- **JetBrains Junie** (`~/.junie/config.json`, `PreToolUse`): Claude Code's tool names, so its
  calls reach the guards as they are, and it replies `decision: ask` or `deny`, so an ask stays an
  ask. Junie runs hooks from your user config only, not a project's.
- **Gemini CLI** (`~/.gemini/settings.json`, `BeforeTool`, off by default): `run_shell_command`,
  `read_file`, `write_file`, `replace` and `mcp_<server>_<tool>`. It replies `decision: deny`, so
  ask becomes deny.

Amp has no command hooks: its only hook point is a TypeScript plugin API, which brainrc doesn't
write yet, so Amp gets your instructions and MCP servers but no guard.
