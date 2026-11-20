"""A pack's [scope] (#140): where it applies, so its deliver checks, guard rules and reviewers stay
out of work it has nothing to do with.

    [scope]
    remotes = ["github.com/acme/*"]      # a git remote of the repo you're in
    paths = ["~/src/acme"]               # the directory you're in, or one above it
    kube_contexts = ["acme-*"]           # kubectl's current context
    aws_profiles = ["acme-*"]            # $AWS_PROFILE ("default" when unset)
    tickets = ["ACME-*"]                 # a ticket ref in the branch name, or one you pass

Every value is a list of globs. The pack applies when any one of them matches; a pack without
[scope], or with an empty one, applies everywhere. The Claude guard hook carries its own copy of
this evaluator (overrides/claude/hooks/guard_outward.py), since it runs without brainrc installed;
tests/test_scope.py keeps the two in step.
"""
from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path

KEYS = ("remotes", "paths", "kube_contexts", "aws_profiles", "tickets")
LABELS = {"remotes": "git remote", "paths": "directory", "kube_contexts": "kube context",
          "aws_profiles": "AWS profile", "tickets": "ticket"}
TICKET = re.compile(r"(?<![A-Za-z0-9])([A-Za-z][A-Za-z0-9]*-\d+)(?![0-9])")
REMOTE_URL = re.compile(r"^\s*url\s*=\s*(.+?)\s*$")
SECTION = re.compile(r"^\s*\[\s*([^\]\s\"]+)(?:\s+\"([^\"]*)\")?\s*\]")


def normalize_remote(url: str) -> str:
    """`git@github.com:acme/app.git`, `https://user@github.com/acme/app` -> `github.com/acme/app`:
    host and path without scheme, user, port or .git, so one glob covers SSH and HTTPS."""
    url = url.strip()
    m = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://(?:[^/@]*@)?([^/:]+)(?::\d+)?/?(.*)$", url)
    if m:
        host, path = m.groups()
    elif (m := re.match(r"^(?:[^@/]+@)?([^/:]+):(.*)$", url)):  # scp-like: [user@]host:path
        host, path = m.groups()
    else:
        return url.lower()
    path = path.strip("/")
    path = path[:-4] if path.endswith(".git") else path
    return f"{host}/{path}".lower().rstrip("/")


def _git_dir(start: Path) -> Path | None:
    """The .git directory of the repo start is in (a worktree's own, for HEAD), or None."""
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
                return g if g.is_absolute() else (d / g)
            return None
    return None


def _common_dir(git_dir: Path) -> Path:
    """Where a worktree's shared config lives (its `commondir`), else git_dir itself."""
    try:
        common = (git_dir / "commondir").read_text(encoding="utf-8").strip()
    except OSError:
        return git_dir
    p = Path(common)
    return p if p.is_absolute() else git_dir / p


def git_remotes(start: Path) -> list[str]:
    """The `url`s of every [remote] in the repo's .git/config, read without running git."""
    git_dir = _git_dir(start)
    if git_dir is None:
        return []
    try:
        lines = (_common_dir(git_dir) / "config").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    urls, in_remote = [], False
    for line in lines:
        if (s := SECTION.match(line)):
            in_remote = s.group(1).lower() == "remote"
        elif in_remote and (u := REMOTE_URL.match(line)):
            urls.append(u.group(1).strip('"'))
    return urls


def git_branch(start: Path) -> str:
    git_dir = _git_dir(start)
    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip() if git_dir else ""
    except OSError:
        return ""
    return head[len("ref: refs/heads/"):] if head.startswith("ref: refs/heads/") else ""


def ticket_refs(text: str) -> list[str]:
    """Ticket refs such as ACME-12 in text (a branch name), upper-cased: `acme-12-fix` -> ACME-12."""
    return [m.upper() for m in TICKET.findall(text)]


def kube_context(env: dict | None = None) -> str:
    """kubectl's current context: the first file in $KUBECONFIG (default ~/.kube/config) that sets
    `current-context`, read as a plain line so no YAML parser is needed."""
    env = os.environ if env is None else env
    files = [f for f in env.get("KUBECONFIG", "").split(os.pathsep) if f] or [str(Path.home() / ".kube" / "config")]
    for f in files:
        try:
            lines = Path(os.path.expanduser(f)).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in lines:
            if line.startswith("current-context:"):
                value = line.split(":", 1)[1].split(" #", 1)[0].strip().strip("'\"")
                if value:
                    return value
    return ""


def aws_profile(env: dict | None = None) -> str:
    env = os.environ if env is None else env
    return env.get("AWS_PROFILE") or env.get("AWS_DEFAULT_PROFILE") or "default"


class Context:
    """Where a command runs: what each [scope] key is matched against, each read once, when first
    asked for (a guard rule that never matches never reads ~/.kube/config)."""

    def __init__(self, cwd: str | Path | None = None, tickets: list[str] | tuple = (), env: dict | None = None):
        self.cwd = Path(os.path.abspath(os.path.expanduser(str(cwd)))) if cwd else Path.cwd()
        self.env = os.environ if env is None else env
        self._extra_tickets = [t.upper() for t in tickets]
        self._cache: dict[str, list[str]] = {}

    def values(self, key: str) -> list[str]:
        if key not in self._cache:
            self._cache[key] = self._read(key)
        return self._cache[key]

    def _read(self, key: str) -> list[str]:
        if key == "remotes":
            urls = git_remotes(self.cwd)
            return [v for u in urls for v in dict.fromkeys((u, normalize_remote(u)))]
        if key == "paths":
            return [os.path.normcase(str(p)) for p in (self.cwd, *self.cwd.parents)]
        if key == "kube_contexts":
            return [c] if (c := kube_context(self.env)) else []
        if key == "aws_profiles":
            return [aws_profile(self.env)]
        if key == "tickets":
            return list(dict.fromkeys(self._extra_tickets + ticket_refs(git_branch(self.cwd))))
        raise KeyError(key)


def _pattern(key: str, glob: str) -> str:
    if key == "paths":  # a separator or case Windows treats as the same still matches
        return os.path.normcase(os.path.normpath(os.path.expandvars(os.path.expanduser(glob))))
    if key in ("remotes", "tickets"):
        return glob.lower() if key == "remotes" else glob.upper()
    return glob


def match(scope: dict | None, ctx: Context) -> tuple[str, str, str] | None:
    """(key, glob, value) for the first glob in scope that matches ctx, None when none does."""
    for key in KEYS:
        globs = (scope or {}).get(key) or []
        for glob in globs if isinstance(globs, list) else []:
            pat = _pattern(key, str(glob))
            for value in ctx.values(key):
                v = value.lower() if key == "remotes" else value
                if fnmatch.fnmatchcase(v, pat):
                    return key, str(glob), value
    return None


def unscoped(scope: dict | None) -> bool:
    """True when scope names no globs at all: the pack applies everywhere."""
    return not any((scope or {}).get(k) for k in KEYS)


def applies(scope: dict | None, ctx: Context) -> bool:
    return unscoped(scope) or match(scope, ctx) is not None


def of(meta: dict) -> dict | None:
    """A pack's [scope] table from its pack.toml, None when it has none (or it isn't a table:
    validate reports that, and the pack then applies everywhere)."""
    s = meta.get("scope")
    return s if isinstance(s, dict) else None


def describe(scope: dict | None) -> str:
    """`git remote github.com/acme/*, or kube context acme-*`; `everywhere` when unscoped."""
    if unscoped(scope):
        return "everywhere"
    parts = [f"{LABELS[k]} {g}" for k in KEYS for g in ((scope or {}).get(k) or [])]
    return ", or ".join(parts)


def check(scope, where: str) -> list[str]:
    """Errors the schema can't express: a glob that is empty."""
    if not isinstance(scope, dict):
        return []
    return [f"{where}: [scope] {k} has an empty glob" for k in KEYS
            if isinstance(scope.get(k), list) and any(isinstance(g, str) and not g.strip() for g in scope[k])]


def cmd_scope(cwd: str | None = None, tickets: list[str] | None = None, extensions: bool = False,
              as_json: bool = False) -> int:
    """`brainrc scope`: which enabled packs apply in a directory, and why; with --extensions, the
    extensions.md a run there should read."""
    import json

    from .config import ConfigError
    from .plugins import render_extensions
    from .sources import sources

    here = Context(cwd, tickets or ())
    if not here.cwd.is_dir():
        print(f"ERROR no directory at {here.cwd}")
        return 1
    try:
        srcs = sources()
        if extensions:
            text = render_extensions(srcs, here)
            if text is None:
                print("ERROR no enabled pack renders extensions (is Gatework enabled?)")
                return 1
            print(text, end="")
            return 0
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    rows = []
    for src in srcs:
        if src.is_core:
            continue
        s = of(src.meta)
        m = match(s, here)
        rows.append({"pack": src.name, "applies": unscoped(s) or m is not None,
                     "why": "no [scope]" if unscoped(s) else
                     f"{LABELS[m[0]]} {m[2]} matches {m[1]}" if m else f"needs {describe(s)}"})
    if as_json:
        print(json.dumps({"cwd": str(here.cwd), "packs": rows}, indent=2))
        return 0
    if not rows:
        print("No packs enabled.")
    for r in rows:
        print(f"{'APPLIES' if r['applies'] else 'SKIPPED':8} {r['pack']}  ({r['why']})")
    return 0
