"""Project scope: a repo with brainrc.toml gets its own agent files, recorded in its brainrc.lock.

The project's packs are core's default packs (unless brainrc.toml turns them off) plus the packs
brainrc.toml adds. Nothing machine-local (packs.local.toml, brainrc.local.toml, *.local.md)
reaches a project's files, so every machine writes the same bytes (docs/project.md).
"""
from __future__ import annotations

import hashlib
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import config, lock, schema
from .config import ConfigError, _read_toml, settings_home, tilde, toml_error
from .packs import describe, fetch_pack, needs_fetch
from .sources import (
    Source, check_packs, collisions, default_packs, duplicate_packs, excluded, items, load_pack,
    markdown_files, rule_text, tree_files,
)

MANIFEST = "brainrc.toml"
SKILLS_DIR = ".agents/skills"
INSTRUCTIONS = "AGENTS.md"
BEGIN = "<!-- brainrc:begin"
END = "<!-- brainrc:end -->"
BLOCK = re.compile(r"<!-- brainrc:begin\b[^\n]*-->\n.*?<!-- brainrc:end -->", re.S)
ORIGIN_KEYS = ("git", "path")
PROJECT_KEYS = ("project_skills", "project_instructions")  # harnesses.toml: where a tool needs its own


def find_project(start: Path | None = None) -> Path | None:
    """The directory holding brainrc.toml: start (default: the current directory) or a parent,
    up to the repo root (the first directory holding `.git`). Outside a repo, start only."""
    here = (start or Path.cwd()).resolve()
    chain = []
    for d in (here, *here.parents):
        chain.append(d)
        if (d / ".git").exists():
            break
    else:
        chain = [here]
    return next((d for d in chain if (d / MANIFEST).is_file()), None)


@dataclass
class Pack:
    key: str
    cfg: dict          # enabled, git/ref or path, as layered
    root: Path         # where its files are (a fetched clone, or a directory)


@dataclass
class Project:
    root: Path
    manifest: dict
    core: dict = field(default_factory=dict)  # core's harnesses.toml, read and checked once by load()

    @property
    def lock_path(self) -> Path:
        return self.root / lock.NAME

    @property
    def exclude(self) -> list[str]:
        return self.manifest.get("exclude", [])

    @property
    def harnesses(self) -> dict[str, dict]:
        """The tools that get their own files (docs/project.md), from core's harnesses.toml only:
        the ones brainrc.toml names, else every enabled one, by name."""
        names = self.manifest["harnesses"] if "harnesses" in self.manifest else \
            [n for n, h in self.core.items() if h.get("enabled", True)]
        return {n: self.core[n] for n in sorted(names)}

    @property
    def skill_dirs(self) -> list[str]:
        """Where skills are copied: .agents/skills/, then each selected tool's own directory."""
        own = {h["project_skills"] for h in self.harnesses.values() if "project_skills" in h} - {SKILLS_DIR}
        return [SKILLS_DIR, *sorted(own)]

    @property
    def skill_tops(self) -> list[str]:
        """Every directory a skill could be copied to, selected or not: how status groups files."""
        return [SKILLS_DIR, *sorted({h["project_skills"] for h in self.core.values() if "project_skills" in h})]

    @property
    def instruction_files(self) -> list[str]:
        """AGENTS.md, then each selected tool's own instructions file, unless it already reads
        AGENTS.md: a link to it, or a file whose own text imports it (`@AGENTS.md`)."""
        found = [INSTRUCTIONS]
        agents = (self.root / INSTRUCTIONS).resolve()
        for rel in sorted({h.get("project_instructions", INSTRUCTIONS) for h in self.harnesses.values()} - {INSTRUCTIONS}):
            path = self.root / rel
            if path.is_symlink() and path.resolve() == agents:
                continue
            own = BLOCK.sub("", path.read_bytes().decode("utf-8")) if _read(path) is not None else ""
            if f"@{INSTRUCTIONS}" in (line.strip() for line in own.splitlines()):
                continue
            found.append(rel)
        return found

    def packs(self) -> list[Pack]:
        """Enabled packs: core's default packs in packs.toml order, then the ones brainrc.toml adds."""
        core = _read_toml(config.REPO / "packs.toml")
        own = self.manifest.get("packs", {})
        found = []
        for key in [*default_packs(), *(k for k in own if k not in default_packs())]:
            cfg, base = dict(core.get(key, {})), config.REPO  # a default pack's path is core's
            if key in own:
                if any(k in own[key] for k in ORIGIN_KEYS):
                    for k in (*ORIGIN_KEYS, "ref"):
                        cfg.pop(k, None)
                    base = self.root
                cfg.update(own[key])
            if cfg.get("enabled", True):
                found.append(Pack(key, cfg, _pack_root(key, cfg, base)))
        return found


def _pack_root(key: str, cfg: dict, base: Path) -> Path:
    if "git" in cfg:  # one clone per URL and ref, shared by every project that pins the same
        tag = hashlib.sha256(f"{cfg['git']}\n{cfg.get('ref', 'HEAD')}".encode()).hexdigest()[:12]
        return settings_home() / "project-packs" / f"{key}-{tag}"
    root = config.expand(str(cfg["path"]))
    return root if root.is_absolute() else base / root


def core_harnesses() -> dict[str, dict]:
    """core's harnesses.toml, never harnesses.local.toml: a project's files can't depend on a machine.
    A `project_*` path must stay inside the repo."""
    found = _read_toml(config.REPO / "harnesses.toml")
    for name, h in found.items():
        for key in PROJECT_KEYS:
            if key in h and not _in_repo(h[key]):
                raise ConfigError(f"harnesses.toml: [{name}] {key} must be a path inside the repo")
    return found


def _in_repo(rel) -> bool:
    """A plain relative path in the repo: no `..`, `.` or empty part, nothing under .git."""
    if not isinstance(rel, str) or "\\" in rel or re.match(r"[~$]|[A-Za-z]:", rel):
        return False
    parts = rel.split("/")
    return all(p not in ("", ".", "..") for p in parts) and parts[0] != ".git"


def load(root: Path) -> Project:
    """The project at root, its brainrc.toml checked against the schema and core's default packs."""
    path = root / MANIFEST
    text = path.read_bytes().decode("utf-8")
    where = tilde(path)
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise toml_error(path, text, e) from None
    problems = schema.errors(data, schema.load("brainrc.toml"))
    for key, cfg in data.get("packs", {}).items() if isinstance(data.get("packs"), dict) else ():
        if isinstance(cfg, dict) and key not in default_packs() and not any(k in cfg for k in ORIGIN_KEYS):
            problems.append(f"packs.{key}: set `git` or `path` ({key} isn't a default pack)")
    core = core_harnesses()  # checks its project paths, so outputs() can't fail on them later
    if not problems and data.get("harnesses"):
        problems += [f"harnesses: unknown harness `{n}` (one of: {', '.join(sorted(core))})"
                     for n in data["harnesses"] if n not in core]
    if problems:
        raise ConfigError(f"{where}: " + "; ".join(problems))
    return Project(root, data, core)


def project_items(src: Source, kind: str, exclude: list[str]) -> list[Path]:
    return [p for p in items(src, kind) if not excluded(src, p, exclude)]


def project_pack_files(project: Project, src: Source) -> dict[str, str]:
    """What the project installs from a pack (docs/project.md): no hooks, and `exclude` from brainrc.toml."""
    return lock.pack_files(src, project_items(src, "skills", project.exclude), False)


def render_block(srcs: list[Source]) -> str | None:
    """The marked block brainrc owns in AGENTS.md: each pack's rules, labelled. None without rules."""
    parts = []
    for src in srcs:
        rules = markdown_files("rules", src)
        if rules:
            parts.append(f"<!-- pack: {src.name} -->\nRules from pack {src.name}.")
            parts += [rule_text(p) for p in rules]
    if not parts:
        return None
    names = ", ".join(s.name for s in srcs)
    head = f"{BEGIN}: generated from {MANIFEST} (packs: {names}). Edit the packs, not this block. -->"
    return "\n\n".join([head, *parts, END])


def with_block(text: str | None, block: str | None) -> str | None:
    """text with brainrc's block replaced, added at the end, or removed; None for no file at all."""
    text = text or ""
    m = BLOCK.search(text)
    if block is not None:
        if m:
            return text[:m.start()] + block + text[m.end():]
        return (text.rstrip("\n") + "\n\n" if text.strip() else "") + block + "\n"
    if not m:
        return text or None
    before, after = text[:m.start()].rstrip("\n"), text[m.end():].lstrip("\n")
    rest = before + ("\n\n" if before and after else "\n" if before else "") + after
    return rest if rest.strip() else None


def import_block() -> str:
    """The block for a tool that reads its own instructions file, not AGENTS.md: an import of it."""
    return f"{BEGIN}: generated from {MANIFEST}. Edit the packs, not this block. -->\n@{INSTRUCTIONS}\n{END}"


def outputs(project: Project, srcs: list[Source]) -> tuple[dict[str, bytes], dict[str, str]]:
    """(whole files by repo path, marked blocks by repo path) that the project's packs produce:
    the standard .agents/skills/ and AGENTS.md first, then a copy only where a selected tool can't
    read them (harnesses.toml `project_skills`, `project_instructions`)."""
    skill_dirs = project.skill_dirs
    files: dict[str, bytes] = {}
    for src in srcs:
        for skill in project_items(src, "skills", project.exclude):
            for rel, f in tree_files(skill):
                data = f.read_bytes()
                for top in skill_dirs:
                    files[f"{top}/{skill.name}/{rel}"] = data
    block = render_block(srcs)
    if not block:
        return files, {}
    return files, {rel: block if rel == INSTRUCTIONS else import_block() for rel in project.instruction_files}


def planned(project: Project, locked: dict) -> list[str]:
    """Where brainrc.toml now puts files (its `harnesses`) against where the lock says they went,
    worked out from the lock's own pack files, so no pack has to be on this machine. One line per
    skill or block, naming brainrc.toml as the cause."""
    want: set[str] = set()
    rules = False
    for entry in locked.get("packs", {}).values():
        for rel in entry["files"]:
            parts = rel.split("/")
            if parts[0] == "skills" and len(parts) > 2:
                want.update(f"{top}/{'/'.join(parts[1:])}" for top in project.skill_dirs)
            rules = rules or parts[0] == "rules"
    have = set(locked.get("outputs", {}))
    errors = set()
    for rel in want ^ have:
        unit = _unit(rel, project.skill_tops)
        errors.add(f"{unit}: {MANIFEST} asks for it, {lock.NAME} doesn't have it (run apply to relock)" if rel in want
                   else f"{unit}: in {lock.NAME}, but {MANIFEST} no longer asks for it (run apply to relock)")
    blocks = set(project.instruction_files) if rules else set()
    for rel in blocks ^ set(locked.get("blocks", {})):
        errors.add(f"{rel}: {MANIFEST} asks for brainrc's block, {lock.NAME} doesn't have it (run apply to relock)"
                   if rel in blocks else
                   f"{rel}: brainrc's block is in {lock.NAME}, but {MANIFEST} no longer asks for it (run apply to relock)")
    return sorted(errors)


def _read(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() and not path.is_symlink() else None


def _linked(root: Path, rel: str) -> bool:
    """True if a directory on the way to root/rel is a link: brainrc never writes or deletes
    through one, so a repo can't point it outside itself."""
    d = root
    for part in rel.split("/")[:-1]:
        d = d / part
        if d.is_symlink():
            return True
    return False


def _unit(rel: str, tops: list[str]) -> str:
    """What a status line names: a skill's directory under one of tops, or the file itself."""
    for top in tops:
        if rel.startswith(top + "/") and "/" in rel[len(top) + 1:]:
            return f"{top}/{rel[len(top) + 1:].split('/')[0]}/"
    return rel


RANK = {"create": 0, "update": 1, "prune": 2, "conflict": 3}


def sync(root: Path, apply: bool) -> int:
    """status (apply=False) or apply for the project at root. Prints its own section."""
    print(f"\nProject {tilde(root)} ({MANIFEST})")
    try:
        project = load(root)
        packs = project.packs()
        old = lock.read(project.lock_path) or {}
    except ConfigError as e:
        print(f"ERROR {e}\n\nNothing written in the project. Fix it, then re-run.")
        return 1
    pending = [p for p in packs if "git" in p.cfg and needs_fetch(p.cfg, p.root)]
    for p in pending:
        print(describe(p.key, p.cfg))
        if apply:
            try:
                fetch_pack(p.key, p.cfg, p.root)
            except ConfigError as e:
                print(f"ERROR {e}\n\nNothing written in the project. Check the pack's `git` and `ref` "
                      f"in {MANIFEST}, then re-run.")
                return 1
    if pending and not apply:
        print("\nDry run. Run `apply` to fetch, then `status` lists the project's files.")
        return 0
    try:
        for p in packs:
            if not p.root.is_dir():
                raise ConfigError(f"pack {p.key}: no directory at {tilde(p.root)}")
        srcs = [load_pack(p.root, p.key) for p in packs]
        problems = duplicate_packs(srcs) + collisions(srcs)
        incompatible, warnings = check_packs(srcs)
    except ConfigError as e:
        problems, incompatible, warnings = [str(e)], [], []
    for w in warnings:
        print(f"WARN {w}")
    if problems or incompatible:
        for e in problems + incompatible:
            print(f"ERROR {e}")
        print("\nNothing written in the project. Fix the packs, then re-run.")
        return 1
    files, blocks = outputs(project, srcs)
    try:
        locked = {p.key: lock.pack_entry(p.cfg, p.root, project_pack_files(project, src)) for p, src in zip(packs, srcs)}
    except ConfigError as e:
        print(f"ERROR {e}\n\nNothing written in the project.")
        return 1
    lock.report_moved(old, {"packs": locked}, "relocked" if apply else "apply relocks it")
    return _write(project, old, files, blocks, apply, locked)


def _write(project: Project, old: dict, files: dict[str, bytes], blocks: dict[str, str], apply: bool,
           locked: dict[str, dict]) -> int:
    owned = old.get("outputs", {})
    tops = project.skill_tops
    states: dict[str, str] = {}
    written: dict[str, str] = {}
    actions: list[tuple[str, str, bytes | None]] = []  # (state, path, bytes or None to delete)
    for rel, data in sorted(files.items()):
        if _linked(project.root, rel):
            states[_unit(rel, tops)] = "conflict"
            continue
        now = _read(project.root / rel)
        if now == data:
            written[rel] = lock.digest(data)
            continue
        state = "create" if now is None and not os.path.lexists(project.root / rel) else \
            "update" if rel in owned and now is not None else "conflict"
        states[_unit(rel, tops)] = max(states.get(_unit(rel, tops), state), state, key=RANK.get)
        if state != "conflict":
            actions.append((state, rel, data))
            written[rel] = lock.digest(data)
    for rel, was in sorted(owned.items()):
        if rel in files or _linked(project.root, rel):
            continue
        now = _read(project.root / rel)
        if now is None:
            continue
        state = "prune" if lock.digest(now) == was else "conflict"
        states[_unit(rel, tops)] = max(states.get(_unit(rel, tops), state), state, key=RANK.get)
        if state == "prune":
            actions.append(("prune", rel, None))
        else:
            written[rel] = was  # still brainrc's to report until it is moved
    block_hashes = {}
    for rel in sorted(set(blocks) | set(old.get("blocks", {}))):
        path = project.root / rel
        if os.path.lexists(path) and _read(path) is None:
            states[rel] = "conflict"
            continue
        current = path.read_bytes().decode("utf-8") if path.is_file() else None
        new = with_block(current, blocks.get(rel))
        if rel in blocks:
            block_hashes[rel] = lock.digest(blocks[rel].encode("utf-8"))
        if new != current:
            states[rel] = "create" if current is None else "prune" if new is None else "update"
            actions.append((states[rel], rel, None if new is None else new.encode("utf-8")))
    for unit, state in sorted(states.items()):
        detail = "  (changed since brainrc wrote it, or not brainrc's; move it, then re-run)" if state == "conflict" else ""
        print(f"{state.upper():9} {'project':9} {unit}{detail}")
    new_lock = lock.new_lock("project", locked, outputs=written, blocks=block_hashes)
    current_lock = project.lock_path.read_bytes() if project.lock_path.is_file() else None
    lock_changes = lock.dumps(new_lock).encode("utf-8") != current_lock
    if apply:
        for state, rel, data in actions:
            path = project.root / rel
            if data is None:
                path.unlink()
                _remove_empty_parents(path.parent, project.root)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        if lock.write(project.lock_path, new_lock):
            print(f"{'LOCK':9} {'project':9} {lock.NAME}")
    elif lock_changes:
        print(f"{'LOCK':9} {'project':9} {lock.NAME}")
    conflicts = sum(s == "conflict" for s in states.values())
    if not states and not (lock_changes and not apply):
        print("Project in sync.")
    elif not apply and (len(states) > conflicts or lock_changes):
        print("\nDry run. Run `apply` to write.")
    if conflicts:
        print(f"\n{conflicts} conflict(s) in the project: files brainrc doesn't own. Move them, then re-run.")
    return 1 if conflicts else 0


def _remove_empty_parents(d: Path, top: Path) -> None:
    while d != top and d.is_dir() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent

