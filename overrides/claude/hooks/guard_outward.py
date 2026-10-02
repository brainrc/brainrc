#!/usr/bin/env python3
"""Claude Code PreToolUse hook for Bash and MCP tools: require confirmation for outward or
destructive actions.

Reads the hook payload (JSON) on stdin. For risky commands, prints a PreToolUse decision of
"ask" so the harness prompts the user even if the model skipped its own approval step.
Everything else produces no output, leaving the normal permission flow unchanged.

Covers git/GitHub, package and image publishing, Terraform/OpenTofu/Terragrunt, Kubernetes,
Helm, Argo CD, Flux, AWS CLI writes and secret reads, database migrations and SQL against
non-local databases, and homelab hypervisor/OS power operations. Commands wrapped in
`sh -c '...'`, `eval`, `$(...)`, or backticks are checked too. MCP tools whose name contains a
write verb (create, update, send, merge, ...) are asked about, except on local-only servers.
Dry runs and clearly local-only operations pass through without a prompt.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

# Up to the end of the current simple command (don't match across ; && || |).
SAME_CMD = r"[^|;&\n]*"
# Verb not glued to a flag, value, or path (so `plan -destroy` and `-out=apply.tfplan` aren't verbs).
VERB = r"(?<![-\w=./])"
VERB_END = r"(?![\w.=/-])"
# git with optional global options before the subcommand: `git -C dir push`, `git -c k=v push`.
GIT = r"\bgit(?:\s+(?:-[Cc]\s+\S+|--[\w-]+(?:=\S+)?))*\s+"

RULES: list[tuple[str, str]] = [
    # git / GitHub
    (GIT + r"push\b", "git push publishes commits"),
    (GIT + r"reset\s+--hard\b", "git reset --hard discards local work"),
    (GIT + r"clean\s+-\w*f", "git clean -f deletes untracked files"),
    (GIT + r"branch\s+-D\b", "git branch -D force-deletes a branch"),
    (r"\bgh\s+pr\s+(create|merge|close|reopen|comment|edit|review|ready)\b", "changes a pull request"),
    (r"\bgh\s+issue\s+(create|comment|edit|close|reopen|delete|transfer|lock)\b", "changes an issue"),
    (r"\bgh\s+release\s+(create|delete|edit|upload)\b", "changes a release"),
    (r"\bgh\s+repo\s+(create|delete|edit|rename|archive)\b", "changes a repository"),
    (r"\bgh\s+(secret|variable)\s+(set|delete)\b", "changes repository secrets or variables"),
    (r"\bgh\s+workflow\s+(run|enable|disable)\b", "triggers or changes CI workflows"),
    # publishing
    (r"\b(npm|pnpm|yarn|bun)\s+publish\b|\bcargo\s+publish\b|\btwine\s+upload\b|\bdocker\s+(push|login)\b",
     "publishes a package or image"),
    # Terraform family
    (rf"\b(terraform|tofu|terragrunt)\b{SAME_CMD}{VERB}(apply|destroy|import|force-unlock|taint|untaint){VERB_END}",
     "changes infrastructure or Terraform state"),
    (rf"\b(terraform|tofu|terragrunt)\b{SAME_CMD}\bstate\s+(rm|mv|push|replace-provider)\b", "edits Terraform state"),
    (rf"\b(terraform|tofu|terragrunt)\b{SAME_CMD}\bworkspace\s+delete\b", "deletes a Terraform workspace"),
    # GitOps controllers
    (r"\bargocd\s+app\s+(sync|delete|rollback|set|terminate-op|patch|create|edit)\b", "changes an Argo CD application"),
    (r"\bargocd\s+(cluster|repo|proj|account)\s+(add|rm|delete|create|set|update)\b", "changes Argo CD configuration"),
    (r"\bflux\s+(reconcile|suspend|resume|delete|create|bootstrap|install|uninstall)\b", "changes Flux state"),
    # AWS: reading secret values into context
    (r"\baws\b" + SAME_CMD + r"\bsecretsmanager\s+get-secret-value\b", "reveals secret values"),
    (r"\baws\b" + SAME_CMD + r"\bssm\s+get-parameters?\b" + SAME_CMD + r"--with-decryption", "reveals secret values"),
    # homelab / hosts
    (r"\b(qm|pct)\s+(destroy|stop|shutdown|reboot|reset|rollback|migrate)\b", "changes Proxmox guests"),
    (r"\btalosctl\b" + SAME_CMD + r"\b(apply-config|upgrade|upgrade-k8s|reset|reboot|shutdown|bootstrap)\b",
     "changes Talos nodes"),
    (r"(^|[;&|]\s*|\bsudo\s+)(reboot|shutdown|poweroff|halt)\b", "reboots or powers off a host"),
]

KUBECTL_MUTATING = {
    "apply", "create", "delete", "patch", "edit", "replace", "scale", "drain", "cordon",
    "uncordon", "label", "annotate", "exec", "set", "expose", "run", "taint", "autoscale", "cp",
}
KUBECTL_READ = {"get", "describe", "logs", "diff", "top", "explain", "config", "version", "rollout",
                "api-resources", "api-versions", "auth", "port-forward", "wait", "events",
                "kustomize", "cluster-info", "debug", "plugin", "completion"}
KUBECTL_ROLLOUT_MUTATING = {"restart", "undo", "pause", "resume"}
HELM_MUTATING = {"install", "upgrade", "uninstall", "delete", "rollback"}
HELM_READ = {"template", "lint", "list", "ls", "status", "history", "get", "show", "search", "repo",
             "dependency", "dep", "package", "pull", "version", "env", "diff", "plugin", "verify"}
AWS_WRITE_VERB = re.compile(
    r"^(create|delete|put|update|modify|terminate|run|start|stop|reboot|attach|detach|associate|"
    r"disassociate|remove|add|register|deregister|set|tag|untag|invoke|publish|send|restore|revoke|"
    r"authorize|reset|enable|disable|import|copy|replace|cancel|deploy|execute|admin-|rotate|purge)"
)
AWS_S3_WRITE = {"cp", "mv", "rm", "sync", "mb", "rb"}
AWS_VALUE_FLAGS_BOOLEAN = {"--debug", "--no-cli-pager", "--no-paginate", "--no-verify-ssl",
                           "--no-sign-request", "--no-cli-auto-prompt"}
MIGRATION_TOOLS = {"migrate", "goose", "atlas", "alembic", "flyway", "dbmate", "sqlx"}
MIGRATION_VERBS = {"up", "down", "apply", "upgrade", "downgrade", "migrate", "redo", "reset",
                   "rollback", "drop", "force", "run"}
LOCAL_DB = re.compile(r"localhost|127\.0\.0\.1|\[::1\]|sqlite|:memory:|file:")
SQL_WRITE = re.compile(r"\b(DROP|TRUNCATE|DELETE|ALTER|UPDATE|INSERT|GRANT|REVOKE)\b", re.I)
GH_API_WRITE_FLAGS = {"-f", "-F", "--field", "--raw-field", "--input"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
SUBSHELL = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")
MAX_DEPTH = 3  # nested sh -c / $(...) levels to unwrap

# MCP tools: `mcp__<server>__<tool>`. A tool name containing one of these words is a write.
MCP_WRITE_WORDS = {
    "create", "update", "delete", "remove", "edit", "add", "merge", "push", "send", "post",
    "publish", "transition", "fork", "schedule", "upload", "write", "set", "assign", "close",
    "reopen", "approve", "archive", "rename", "move", "cancel", "trigger", "invite", "reply",
}
# Servers whose writes stay on this machine.
MCP_LOCAL_SERVERS = ("memory", "sequential-thinking", "sequential_thinking", "context7")


def _tokens(command: str) -> list[str]:
    """Shell-ish tokens; operators split out even without spaces (`ls;kubectl delete ...`)."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:  # unbalanced quotes: fall back to whitespace split
        return command.split()


def _segments(tokens: list[str]) -> list[list[str]]:
    """Split a token list into simple commands on shell operators."""
    segments, current = [], []
    for tok in tokens:
        if tok and set(tok) <= set(";&|()"):
            segments.append(current)
            current = []
        else:
            current.append(tok)
    segments.append(current)
    return [s for s in segments if s]


def _inner_commands(command: str, segments: list[list[str]]) -> list[str]:
    """Command strings hidden inside `sh -c '...'`, `eval ...`, `$(...)`, and backticks."""
    inner = [a or b for a, b in SUBSHELL.findall(command)]
    for seg in segments:
        for i, tok in enumerate(seg):
            prog = _prog(tok)
            if prog in SHELLS:
                for j in range(i + 1, len(seg) - 1):
                    flag = seg[j]
                    if not flag.startswith("-") or flag == "--":
                        break
                    if "c" in flag.lstrip("-") and not flag.startswith("--"):
                        inner.append(seg[j + 1])
                        break
            elif prog == "eval":
                inner.append(" ".join(seg[i + 1:]))
    return inner


def _dry_run(seg: list[str]) -> bool:
    """`--dry-run`, `--dry-run=client|server`; `--dry-run=none` is a real run."""
    return any(t == "--dry-run" or (t.startswith("--dry-run=") and t.split("=", 1)[1] != "none")
               for t in seg)


def _words(segment: list[str], start: int) -> list[str]:
    return [t for t in segment[start:] if not t.startswith("-")]


def _subcommand(segment: list[str], start: int, known: set[str]) -> tuple[str | None, list[str]]:
    """First known subcommand after `start` (skips global flags and their values), plus what follows."""
    words = _words(segment, start)
    for n, word in enumerate(words):
        if word in known:
            return word, words[n + 1:]
    return None, []


def _prog(tok: str) -> str:
    return tok.rsplit("/", 1)[-1]


def _rm_recursive_force(seg: list[str], i: int) -> bool:
    recursive = force = False
    for flag in seg[i + 1:]:
        if not flag.startswith("-") or flag == "--":
            break
        short = not flag.startswith("--")
        if flag == "--recursive" or (short and set("rR") & set(flag)):
            recursive = True
        if flag == "--force" or (short and "f" in flag):
            force = True
    return recursive and force


def _gh_api_write(seg: list[str], i: int) -> bool:
    rest = seg[i + 2:]
    if "graphql" in _words(seg, i + 2)[:1]:
        # GraphQL always POSTs with -f; only mutations write. --input hides the body, so ask.
        return any(t == "--input" for t in rest) or any(re.search(r"\bmutation\b", t) for t in rest)
    for j, tok in enumerate(rest):
        if tok in GH_API_WRITE_FLAGS:
            return True
        method = None
        if tok in ("-X", "--method") and j + 1 < len(rest):
            method = rest[j + 1]
        elif tok.startswith("--method="):
            method = tok.split("=", 1)[1]
        elif tok.startswith("-X") and len(tok) > 2:
            method = tok[2:]
        if method and method.upper() != "GET":
            return True
    return False


def _aws_write(seg: list[str], i: int) -> bool:
    words, skip = [], False
    for tok in seg[i + 1:]:
        if skip:
            skip = False
            continue
        if tok.startswith("--"):
            skip = "=" not in tok and tok not in AWS_VALUE_FLAGS_BOOLEAN and not words
            continue
        words.append(tok)
        if len(words) == 2:
            break
    if len(words) < 2:
        return False
    service, op = words
    if service == "s3":
        return op in AWS_S3_WRITE
    return bool(AWS_WRITE_VERB.match(op))


def _segment_reason(seg: list[str], raw: str) -> str | None:
    for i, tok in enumerate(seg):
        prog = _prog(tok)
        dry_run = _dry_run(seg)
        if prog == "rm" and _rm_recursive_force(seg, i):
            return "rm -rf deletes files recursively"
        if prog == "gh" and seg[i + 1:i + 2] == ["api"] and _gh_api_write(seg, i):
            return "gh api call that writes to GitHub"
        if prog == "kubectl" and not dry_run:
            sub, rest = _subcommand(seg, i + 1, KUBECTL_MUTATING | KUBECTL_READ)
            if sub in KUBECTL_MUTATING or (sub == "rollout" and rest[:1] and rest[0] in KUBECTL_ROLLOUT_MUTATING):
                return f"kubectl {sub} changes cluster state"
        if prog == "helm" and not dry_run:
            sub, _ = _subcommand(seg, i + 1, HELM_MUTATING | HELM_READ)
            if sub in HELM_MUTATING:
                return f"helm {sub} changes a release"
        if prog == "aws" and _aws_write(seg, i):
            return "AWS CLI call that changes resources"
        if prog in MIGRATION_TOOLS and set(_words(seg, i + 1)) & MIGRATION_VERBS and not LOCAL_DB.search(raw):
            return "runs database migrations against a non-local database"
        if prog == "psql" and SQL_WRITE.search(raw) and not LOCAL_DB.search(raw):
            return "SQL that changes data or schema on a non-local database"
    return None


def reason_for(command: str, depth: int = 0) -> str | None:
    for pattern, reason in RULES:
        if re.search(pattern, command):
            return reason
    segments = _segments(_tokens(command))
    for seg in segments:
        reason = _segment_reason(seg, " ".join(seg))
        if reason:
            return reason
    if depth < MAX_DEPTH:
        for inner in _inner_commands(command, segments):
            reason = reason_for(inner, depth + 1)
            if reason:
                return reason
    return None


def mcp_reason(tool_name: str) -> str | None:
    """Ask before MCP tools that write to an outside system (create_pull_request, sendMessage, ...)."""
    parts = tool_name.split("__")
    if len(parts) < 3:
        return None
    server, tool = parts[1], parts[-1]
    if server.lower().endswith(MCP_LOCAL_SERVERS):
        return None
    words = {w.lower() for w in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", tool)}
    if words & MCP_WRITE_WORDS:
        return f"MCP tool {tool} writes to {server}"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # malformed payload: defer to the harness's normal permission flow
    tool_name = str(payload.get("tool_name", ""))
    if tool_name == "Bash":
        reason = reason_for(str(payload.get("tool_input", {}).get("command", "")))
    elif tool_name.startswith("mcp__"):
        reason = mcp_reason(tool_name)
    else:
        return 0
    if reason:
        json.dump({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"ai-config guard: {reason}. Confirm this is approved.",
            }
        }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
