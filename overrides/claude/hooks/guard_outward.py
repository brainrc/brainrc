#!/usr/bin/env python3
"""Claude Code PreToolUse hook for Bash and MCP tools: require confirmation for outward or
destructive actions.

Reads the hook payload (JSON) on stdin. For risky commands, prints a PreToolUse decision of
"ask" so the harness prompts the user even if the model skipped its own approval step.
Everything else produces no output, leaving the normal permission flow unchanged.

Covers git/GitHub, package and image publishing, Terraform/OpenTofu/Terragrunt, Kubernetes,
Helm, Argo CD, Flux, AWS CLI writes and secret reads, database migrations and SQL against
non-local databases, and host reboot/poweroff. Commands wrapped in
`sh -c '...'`, `eval`, `$(...)`, or backticks are checked too. MCP tools whose name contains a
write verb (create, update, send, merge, ...) are asked about, except on local-only servers.
Dry runs and clearly local-only operations pass through without a prompt.

Packs add rules of their own as [[guard.deny]] and [[guard.ask]] in pack.toml (#141): `brainrc
apply` renders them, each with its pack's [scope], into $BRAINRC_HOME/guard-rules.json, and this
hook matches them against every command it unwraps and every MCP tool name. A deny from a pack
wins over any ask; a rule whose scope doesn't match where the command runs is skipped.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import sys
from pathlib import Path

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
    # hosts (Proxmox and Talos rules: examples/pack-homelab)
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


# Pack rules (#141). The [scope] evaluator below is a copy of brainrc/scope.py, which this hook can't
# import (it runs without brainrc installed); tests/test_scope.py checks the two agree.
SCOPE_KEYS = ("remotes", "paths", "kube_contexts", "aws_profiles", "tickets")
TICKET = re.compile(r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9]*-\d+)(?![0-9])")
REMOTE_URL = re.compile(r"^\s*url\s*=\s*(.+?)\s*$", re.I)
SECTION = re.compile(r"^\s*\[\s*([^\]\s\"]+)(?:\s+\"([^\"]*)\")?\s*\]")
# Commands that run another one, with their options that take a value (short letters, long names);
# timeout also takes a duration before the command.
WRAPPERS: dict[str, tuple[str, set[str]]] = {
    "sudo": ("ugChpUDRTrt", {"--user", "--group", "--chdir", "--host", "--prompt", "--other-user",
                             "--role", "--type", "--close-from", "--command-timeout"}),
    "doas": ("uC", set()),
    "env": ("uCS", {"--unset", "--chdir", "--split-string"}),
    "nice": ("n", {"--adjustment"}),
    "timeout": ("sk", {"--signal", "--kill-after"}),
    "time": ("fo", {"--format", "--output"}),
    "exec": ("a", set()),
    "command": ("", set()),
    "nohup": ("", set()),
}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def settings_home() -> Path:
    """brainrc's settings home: $BRAINRC_HOME, $XDG_CONFIG_HOME/brainrc (absolute), ~/.config/brainrc."""
    if os.environ.get("BRAINRC_HOME"):
        return Path(os.path.expandvars(os.path.expanduser(os.environ["BRAINRC_HOME"])))
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    return Path(xdg) / "brainrc" if os.path.isabs(xdg) else Path.home() / ".config" / "brainrc"


def load_pack_rules() -> list[dict]:
    """The rules `brainrc apply` rendered; [] when there are none or the file can't be read."""
    try:
        data = json.loads((settings_home() / "guard-rules.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    rules = data.get("rules") if isinstance(data, dict) else None
    return [r for r in rules if isinstance(r, dict) and r.get("action") in ("deny", "ask")] \
        if isinstance(rules, list) else []


def normalize_remote(url: str) -> str:
    url = url.strip()
    m = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://(?:[^/@]*@)?([^/:]+)(?::\d+)?/?(.*)$", url)
    if m:
        host, path = m.groups()
    elif (m := re.match(r"^(?:[^@/]+@)?([^/:]+):(.*)$", url)):
        host, path = m.groups()
    else:
        return url.lower()
    path = path.strip("/")
    path = path[:-4] if path.endswith(".git") else path
    return f"{host}/{path}".lower().rstrip("/")


def _git_dir(start: Path) -> Path | None:
    for d in (start, *start.parents):
        dot = d / ".git"
        if dot.is_dir():
            return dot
        if dot.is_file():
            try:
                text = dot.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                return None
            if text.startswith("gitdir:"):
                g = Path(text[7:].strip())
                return g if g.is_absolute() else d / g
            return None
    return None


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _scope_values(key: str, cwd: Path) -> list[str]:
    if key == "remotes":
        git_dir = _git_dir(cwd)
        if git_dir is None:
            return []
        common = _read(git_dir / "commondir").strip()
        config_dir = (Path(common) if os.path.isabs(common) else git_dir / common) if common else git_dir
        urls, in_remote = [], False
        for line in _read(config_dir / "config").splitlines():
            if (sec := SECTION.match(line)):
                in_remote = sec.group(1).lower() == "remote"
            elif in_remote and (u := REMOTE_URL.match(line)):
                urls.append(u.group(1).strip('"'))
        return [v for u in urls for v in dict.fromkeys((u, normalize_remote(u)))]
    if key == "paths":
        return [os.path.normcase(str(p)) for p in (cwd, *cwd.parents)]
    if key == "kube_contexts":
        files = [f for f in os.environ.get("KUBECONFIG", "").split(os.pathsep) if f] \
            or [str(Path.home() / ".kube" / "config")]
        for f in files:
            for line in _read(Path(os.path.expanduser(f))).splitlines():
                if line.startswith("current-context:"):
                    value = line.split(":", 1)[1].split(" #", 1)[0].strip().strip("'\"")
                    if value:
                        return [value]
        return []
    if key == "aws_profiles":
        return [os.environ.get("AWS_PROFILE") or os.environ.get("AWS_DEFAULT_PROFILE") or "default"]
    if key == "tickets":
        git_dir = _git_dir(cwd)
        head = _read(git_dir / "HEAD").strip() if git_dir else ""
        branch = head[len("ref: refs/heads/"):] if head.startswith("ref: refs/heads/") else ""
        return list(dict.fromkeys(t.upper() for t in TICKET.findall(branch)))
    return []


def _scope_pattern(key: str, glob: str) -> str:
    if key == "paths":
        return os.path.normcase(os.path.normpath(os.path.expandvars(os.path.expanduser(glob))))
    return glob.lower() if key == "remotes" else glob.upper() if key == "tickets" else glob


def scope_applies(scope, cwd: Path, cache: dict) -> bool:
    """True when scope names no globs, or one of them matches where the command runs."""
    if not isinstance(scope, dict) or not any(scope.get(k) for k in SCOPE_KEYS):
        return True
    for key in SCOPE_KEYS:
        globs = scope.get(key)
        for glob in globs if isinstance(globs, list) else []:
            if key not in cache:
                cache[key] = _scope_values(key, cwd)
            pat = _scope_pattern(key, str(glob))
            if any(fnmatch.fnmatchcase(v.lower() if key == "remotes" else v, pat) for v in cache[key]):
                return True
    return False


def _command_run(seg: list[str]) -> list[str]:
    """The command a simple command runs, from its program on: past VAR=value prefixes and
    wrappers such as sudo, env or timeout, with their options and values (`sudo -u deploy x`,
    `timeout 60 x`). `env -S 'x y'` runs the split string."""
    i = 0
    while i < len(seg):
        tok = seg[i]
        if ASSIGNMENT.match(tok):
            i += 1
            continue
        wrapper = WRAPPERS.get(_prog(tok))
        if wrapper is None:
            return seg[i:]
        letters, long_opts = wrapper
        i += 1
        while i < len(seg) and seg[i].startswith("-") and seg[i] != "-":
            opt = seg[i]
            i += 1
            if opt == "--":
                break
            if opt.startswith("--"):
                name, inline = opt.split("=", 1)[0], "=" in opt
                value = opt.split("=", 1)[1] if inline else (seg[i] if i < len(seg) else "")
                if name in long_opts and not inline:
                    i += 1
                if name == "--split-string" and _prog(tok) == "env":
                    return _split(value) + seg[i:]
                continue
            k = next((n for n, c in enumerate(opt[1:], 1) if c in letters), None)
            if k is not None:  # e.g. -u deploy, -udeploy, -Eu deploy
                value = opt[k + 1:] or (seg[i] if i < len(seg) else "")
                if not opt[k + 1:]:
                    i += 1
                if opt[k] == "S" and _prog(tok) == "env":
                    return _split(value) + seg[i:]
        if _prog(tok) == "timeout" and i < len(seg):
            i += 1  # the duration
    return []


def _split(text: str) -> list[str]:
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


def rule_matches(words: list[str], seg: list[str]) -> bool:
    """The program is words[0] (by name, any directory), and the rest follow it in order, each a glob."""
    run = _command_run(seg)
    if not run or not words or not fnmatch.fnmatchcase(_prog(run[0]), _prog(words[0])):
        return False
    rest = iter(run[1:])
    return all(any(fnmatch.fnmatchcase(tok, w) for tok in rest) for w in words[1:])


def _all_segments(command: str, depth: int = 0):
    """Each simple command, then those hidden in sh -c, eval, $(...) and backticks, MAX_DEPTH deep."""
    segments = _segments(_tokens(command))
    yield from segments
    if depth < MAX_DEPTH:
        for inner in _inner_commands(command, segments):
            yield from _all_segments(inner, depth + 1)


def pack_rule(tool_name: str, command: str, rules: list[dict], cwd) -> dict:
    """{"deny": (pack, reason), "ask": (pack, reason)} for the first rule of each kind that matches
    this call where it runs; {} when none does."""
    if tool_name == "Bash":
        segments = list(_all_segments(command))
        hits = [r for r in rules if isinstance(r.get("match"), list) and r["match"]
                and any(rule_matches([str(w) for w in r["match"]], seg) for seg in segments)]
    else:
        hits = [r for r in rules if isinstance(r.get("tool"), str) and fnmatch.fnmatchcase(tool_name, r["tool"])]
    found, cache = {}, {}
    where = Path(os.path.abspath(str(cwd))) if cwd else Path.cwd()
    for rule in hits:
        action = rule["action"]
        if action not in found and scope_applies(rule.get("scope"), where, cache):
            found[action] = (str(rule.get("pack", "a")), str(rule.get("reason", "a pack guard rule")))
    return found


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # malformed payload: defer to the harness's normal permission flow
    if not isinstance(payload, dict):
        return 0
    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    command = str(tool_input.get("command", ""))
    if tool_name != "Bash" and not tool_name.startswith("mcp__"):
        return 0
    rules = load_pack_rules()
    found = pack_rule(tool_name, command, rules, payload.get("cwd")) if rules else {}
    if "deny" in found:
        pack, reason = found["deny"]
        return _decide("deny", f"brainrc guard ({pack} pack): {reason}. The {pack} pack doesn't allow this.")
    reason = reason_for(command) if tool_name == "Bash" else mcp_reason(tool_name)
    if not reason and "ask" in found:
        pack, why = found["ask"]
        reason = f"{why} ({pack} pack)"
    if reason:
        return _decide("ask", f"brainrc guard: {reason}. Confirm this is approved.")
    return 0


def _decide(decision: str, reason: str) -> int:
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
