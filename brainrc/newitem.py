"""`brainrc new skill|agent|rule NAME` (E8, #159 to #161): an item that validates, inside a pack.

Run in a pack (or name one with --pack): the prefix is applied, the frontmatter filled in and the
body taken from brainrc/_templates/items; brainrc.scaffold renders and writes it, as it does for
`new pack` and `import`. Then the pack is checked as `validate --pack` does. Asks for a missing
description when stdin is a terminal.
"""
from __future__ import annotations

import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .config import KNOWN_MODELS, KNOWN_TOOLS, MODEL_ID, ConfigError, expand, tilde, write_text_atomic
from .naming import NAME
from .scaffold import Agent, Rule, Skill, _toml_string, add_files, agent_text, render_rule, skill_text
from .sources import Source, load_pack, markdown_files

TEMPLATES = Path(__file__).resolve().parent / "_templates" / "items"
KINDS = ("skill", "agent", "rule")
AGENT_TOOLS = "Read, Grep, Glob"  # least privilege: it reads; add Edit, Write or Bash when it must
AGENT_MODEL = "inherit"
RULE_NN = re.compile(r"^(\d+)-")
NAME_MAX = 64  # a skill's name (validate), and so any item's


@dataclass
class Item:
    kind: str
    name: str                # as given: with or without the pack's prefix
    description: str = ""
    domain: list[str] = field(default_factory=list)  # skill: the globs that make it a domain skill
    tools: str = AGENT_TOOLS
    model: str = AGENT_MODEL


def find_pack(where: str | None) -> Source:
    """The pack at --pack, or the nearest folder from here up that has a pack.toml."""
    if where:
        return load_pack(expand(where).resolve())
    here = Path.cwd().resolve()
    for folder in (here, *here.parents):
        if (folder / "pack.toml").is_file():
            return load_pack(folder)
    raise ConfigError("not inside a pack (no pack.toml here or above): cd into one, pass --pack DIR, "
                      "or start one with `brainrc new pack`")


def slug_of(name: str, src: Source, kind: str) -> str:
    """The name after the pack's prefix: `deploy` and `acme-deploy` are the same skill in acme."""
    slug = name.removeprefix(src.prefix) if kind != "rule" else name
    if not NAME.fullmatch(slug):
        raise ConfigError(f"{kind} name `{name}` must be ASCII lowercase letters, digits and hyphens")
    if kind != "rule" and len(src.prefix + slug) > NAME_MAX:
        raise ConfigError(f"{kind} name `{src.prefix}{slug}` is over {NAME_MAX} characters")
    return slug


def _fill(rel: str, values: dict[str, str]) -> str:
    text = (TEMPLATES / rel).read_text(encoding="utf-8")
    return re.sub(r"\{\{([a-z_]+)\}\}", lambda m: values[m.group(1)], text)


def next_rule_number(src: Source) -> str:
    """The first free NN after the pack's last rule, rounded up to the next ten so there is room
    to insert one later (10, 20...), with as many digits as its rules use."""
    found = [m[1] for p in markdown_files("rules", src) if (m := RULE_NN.match(p.name))]
    if not found:
        return "10"
    width = max(len(n) for n in found)
    last = max(int(n) for n in found)
    nn = (last // 10 + 1) * 10
    if nn >= 10 ** width:
        nn = last + 1
    if nn >= 10 ** width:
        raise ConfigError(f"rules/: no number left after {last:0{width}d}; renumber the rules first")
    return f"{nn:0{width}d}"


def domains_row(text: str, globs: list[str], name: str) -> str:
    """pack.toml with a [[extensions.gatework.domains]] row for the skill at the end, unless a row
    already names it; the rest of the file as written."""
    meta = tomllib.loads(text)
    rows = meta.get("extensions", {}).get("gatework", {}).get("domains", [])
    if any(isinstance(r, dict) and name in r.get("skills", []) for r in rows if isinstance(rows, list)):
        return text
    files = ", ".join(f"`{g}`" for g in globs)
    row = f"[[extensions.gatework.domains]]\nfiles = {_toml_string(files)}\nskills = [{_toml_string(name)}]\n"
    after = f"{text.rstrip(chr(10))}\n\n{row}" if text.strip() else row
    tomllib.loads(after)  # fail loudly rather than write a pack.toml nothing can read
    return after


def render(src: Source, item: Item) -> tuple[dict[str, str], str]:
    """(files to write, path of the item) for item in the pack src. pack.toml is among the files
    when a domain skill adds its Domains row."""
    slug = slug_of(item.name, src, item.kind)
    name = f"{src.prefix}{slug}"
    if item.kind == "rule":
        title = slug.replace("-", " ").capitalize()
        rel = f"rules/{next_rule_number(src)}-{slug}.md"
        taken = [p.name for p in markdown_files("rules", src) if p.name.split("-", 1)[-1] == f"{slug}.md"]
        if taken:
            raise ConfigError(f"rules/{taken[0]} already exists; pick another name")
        return {rel: render_rule(Rule(slug, _fill("rule.md", {"title": title})), frontmatter=True)}, rel
    if not item.description:
        raise ConfigError(f"give the {item.kind} a --description: what it does and when to use it")
    values = {"name": name, "description": " ".join(item.description.split())}
    if item.kind == "skill":
        body = "skill.md"
        if item.domain:
            body, values["files"] = "domain-skill.md", ", ".join(f"`{g}`" for g in item.domain)
        rel = f"skills/{name}/SKILL.md"
        files = {rel: skill_text(name, Skill(slug, item.description, _fill(body, values)))}
        if item.domain:
            files["pack.toml"] = domains_row((src.root / "pack.toml").read_text(encoding="utf-8"), item.domain, name)
        return files, rel
    if item.kind == "agent":
        tools = [t.strip() for t in item.tools.split(",") if t.strip()]
        unknown = [t for t in tools if t not in KNOWN_TOOLS and not t.startswith("mcp__")]
        if unknown:
            raise ConfigError(f"--tools: unknown tool {', '.join(unknown)} (known: {', '.join(sorted(KNOWN_TOOLS))})")
        if item.model not in KNOWN_MODELS and not MODEL_ID.match(item.model):
            raise ConfigError(f"--model: unknown model `{item.model}` ({' | '.join(sorted(KNOWN_MODELS))}, or a full ID)")
        rel = f"agents/{name}.md"
        return {rel: agent_text(name, Agent(slug, item.description, _fill("agent.md", values),
                                            tools=", ".join(tools), model=item.model))}, rel


def _ask(question: str, default: str = "") -> str:
    try:
        line = input(f"{question}{f' [{default}]' if default else ''}: ")
    except EOFError:
        print()
        return default
    return line.strip() or default


def ask(item: Item, src: Source) -> Item:
    """Ask for what the command line didn't give: the name and the description."""
    while not item.name:
        item.name = _ask(f"{item.kind.capitalize()} name (after the prefix {src.prefix})")
    if item.kind == "skill" and not item.description and item.domain:
        item.description = default_description(item)
    while item.kind != "rule" and not item.description:
        item.description = _ask("Description: what it does, and when to use it")
    return item


def default_description(item: Item) -> str:
    where = ", ".join(f"`{g}`" for g in item.domain)
    return (f"Offline checks, conventions and a review checklist for {where}. Use when writing, "
            "changing or reviewing those files.")


def token_report(src: Source, rel: str) -> str:
    """What the new rule costs, and the pack's always-loaded tokens against its budget (#161)."""
    from .tokens import always_tokens, source_budget
    total, items = always_tokens(load_pack(src.root))
    mine = next((n for n, label in items if label.endswith(rel)), 0)
    budget = source_budget(src)
    head = f"The rule adds ~{mine} tokens to every session; the pack now loads ~{total}"
    if budget is None:
        return f"{head} (no `max_always_tokens` budget in pack.toml)."
    over = ". Over budget: shorten a rule or move its detail into a skill" if total > budget else ""
    return f"{head} of its {int(budget)}{over}."


def cmd_new_item(kind: str, name: str | None = None, pack: str | None = None, description: str = "",
                 domain: list[str] | None = None, tools: str | None = None, model: str | None = None,
                 yes: bool = False,
                 force: bool = False, dry_run: bool = False) -> int:
    try:
        src = find_pack(pack)
        item = Item(kind, name or "", description, domain or [], tools if tools is not None else AGENT_TOOLS,
                    model or AGENT_MODEL)
        if kind != "skill" and domain:
            raise ConfigError("--domain is for a skill")
        if kind != "agent" and (tools is not None or model):
            raise ConfigError("--tools and --model are for an agent")
        if not yes and sys.stdin.isatty():
            item = ask(item, src)
        elif not item.name:
            raise ConfigError(f"name the {kind}: `brainrc new {kind} <name>`")
        if kind == "skill" and item.domain and not item.description:
            item.description = default_description(item)
        files, rel = render(src, item)
        if dry_run:
            for path in files:
                print(f"  would {'change' if path == 'pack.toml' else 'write'} {path}")
            print(f"Would add {rel} to the pack {src.name} at {tilde(src.root)}.")
            return 0
        add_files(src.root, {k: v for k, v in files.items() if k != "pack.toml"}, force=force)
        if "pack.toml" in files and files["pack.toml"] != (src.root / "pack.toml").read_text(encoding="utf-8"):
            write_text_atomic(src.root / "pack.toml", files["pack.toml"])
            print(f"Added a Domains row for {', '.join(f'`{g}`' for g in item.domain)} to pack.toml.")
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    except OSError as e:
        print(f"ERROR {tilde(Path(e.filename)) + ': ' if e.filename else ''}{e.strerror or e}")
        return 1
    print(f"Wrote {rel} in the pack {src.name} at {tilde(src.root)}.")
    if kind == "rule":
        print(token_report(src, rel))
    from .validate import cmd_validate
    return cmd_validate(pack=str(src.root))
