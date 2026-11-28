"""`brainrc new pack` (#150): a new pack that validates on its first run.

The layout is brainrc/_templates/pack (its README.txt says how a template becomes a file), written
by brainrc.scaffold, the writer `brainrc import` uses too. Asks for what isn't given on the command
line when stdin is a terminal; otherwise, and with --yes, it takes the defaults.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import config
from .config import ConfigError, expand, load_harnesses, tilde
from .naming import name_errors
from .scaffold import PackSpec, Rule, Skill, check_dest, check_name, render_pack, write_pack

TEMPLATES = Path(__file__).resolve().parent / "_templates" / "pack"
BODIES = {"README.txt", "rule.md", "facts.md"}  # read into the pack's rule and skill, not copied
ONLY_FOR = {"CLAUDE.md": "claude", "GEMINI.md": "gemini"}  # the AGENTS.md pointer for tools that need one
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")
# Ticket system -> Gatework's connector for it; "none" writes no [extensions.gatework.ticket].
TICKETS = {"none": "", "github": "brainrc-ticket-github", "jira": "brainrc-ticket-jira",
           "local": "brainrc-ticket-local"}
MAX_ALWAYS_TOKENS = 800
ROOT_ONLY = (".github/workflows/validate.yml", ".pre-commit-config.yaml")  # work only at a repo's root
NOTES = {
    "prefix": "every skill, agent, command and MCP server starts with this",
    "requires_api": "the brainrc pack API versions this pack works with",
    "max_always_tokens": "budget for what loads in every session: rules and descriptions",
    "test": "tests that `brainrc validate --pack` runs",
}


@dataclass
class Answers:
    name: str
    prefix: str = ""
    pack_id: str = ""
    description: str = ""
    harnesses: list[str] = field(default_factory=list)
    ticket: str = "none"
    refs: list[str] = field(default_factory=list)
    host: str = ""  # Jira's site, which its connector needs


def default_prefix(name: str, pack_id: str = "") -> str:
    """`<name>-`, or `<owner>-` for a pack published under an ID (naming rule 2)."""
    return f"{pack_id.split('/')[0]}-" if pack_id else f"{name}-"


def default_refs(ticket: str, name: str) -> list[str]:
    if ticket == "jira":
        key = re.sub(r"[^A-Z0-9]", "", name.upper())
        return [f"{key if key[:1].isalpha() else 'PROJ'}-*"]
    return {"github": ["gh:*"], "local": ["local:*"]}.get(ticket, [])


def core_tag() -> str:
    from .sources import core_version
    return "v" + ".".join(map(str, core_version()))


def _fill(text: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda m: values[m.group(1)], text)


def _template(rel: str) -> str:
    return (TEMPLATES / rel).read_text(encoding="utf-8")


def spec_for(a: Answers) -> PackSpec:
    """The new pack, ready for render_pack: pack.toml's keys, its first rule, its facts skill, and
    the other template files."""
    prefix = a.prefix or default_prefix(a.name, a.pack_id)
    description = a.description or f"Rules and facts for {a.name}'s AI coding agents."
    values = {"name": a.name, "prefix": prefix, "description": description, "core_tag": core_tag(),
              "facts": f"{prefix}facts"}
    spec = PackSpec(a.name, prefix, description, id=a.pack_id, max_always_tokens=MAX_ALWAYS_TOKENS,
                    test="tests", notes=NOTES)
    spec.rules = [Rule(a.name, _fill(_template("rule.md"), values))]
    spec.skills = [Skill("facts", f"Facts about {a.name}: its repositories, hosts, tools and teams. Use "
                         "when a task needs one of them, instead of guessing.", _fill(_template("facts.md"), values))]
    if TICKETS[a.ticket]:
        spec.ticket = {"connector": TICKETS[a.ticket], "refs": a.refs or default_refs(a.ticket, a.name)}
        if a.ticket == "jira":
            if not a.host:
                raise ConfigError("a Jira pack needs its site: --host <name>.atlassian.net")
            spec.ticket["host"] = a.host
    for path in sorted(TEMPLATES.rglob("*")):
        rel = path.relative_to(TEMPLATES).as_posix()
        if not path.is_file() or rel in BODIES or "__pycache__" in rel:
            continue
        if rel in ONLY_FOR and ONLY_FOR[rel] not in a.harnesses:
            continue
        out = "/".join("." + part[4:] if part.startswith("dot-") else part for part in rel.split("/"))
        spec.files[out] = _fill(path.read_text(encoding="utf-8"), values)
    return spec


def _ask(question: str, default: str) -> str:
    try:
        line = input(f"{question}{f' [{default}]' if default else ''}: ")
    except EOFError:
        print()
        return default
    return line.strip() or default


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def ask(a: Answers, given: set[str], known: list[str]) -> Answers:
    """Ask for each answer the command line didn't give; re-ask the ones that break a rule."""
    if a.pack_id:  # never asked, so a bad one stops here rather than in a loop that can't fix it
        errors = name_errors("pack", default_prefix("pack", a.pack_id), a.pack_id, "--id")
        if errors:
            raise ConfigError("; ".join(errors))
    typed = False  # a prefix that isn't the default follows the name when the name is asked again
    while True:
        if "name" not in given:
            a.name = _ask("Pack name (lowercase letters, digits and hyphens)", a.name)
        if "prefix" not in given:
            default = default_prefix(a.name, a.pack_id)
            a.prefix = _ask("Prefix for its skills, agents and commands", a.prefix if typed else default)
            typed = a.prefix != default
        try:
            check_name(a.name, a.prefix, a.pack_id)
            break
        except ConfigError as e:
            if "name" in given:  # asking only for the prefix again can't fix the name
                raise
            print(f"  {e}")
    while "harnesses" not in given:
        a.harnesses = _split(_ask("Harnesses you'll edit it with (for CLAUDE.md and GEMINI.md)",
                                  ",".join(a.harnesses)))
        unknown = [h for h in a.harnesses if h not in known]
        if not unknown:
            break
        print(f"  unknown: {', '.join(unknown)} (known: {', '.join(known)})")
    while "ticket" not in given:
        a.ticket = _ask(f"Ticket system for Gatework ({', '.join(TICKETS)})", a.ticket).lower()
        if a.ticket in TICKETS:
            break
        print(f"  pick one of {', '.join(TICKETS)}")
    while a.ticket == "jira" and "host" not in given and not a.host:
        a.host = _ask("Jira site (e.g. acme.atlassian.net)", "")
    if TICKETS[a.ticket] and "refs" not in given:
        a.refs = _split(_ask("Ticket refs it handles", ",".join(default_refs(a.ticket, a.name))))
    return a


def cmd_new_pack(name: str | None = None, to: str | None = None, prefix: str = "", pack_id: str = "",
                 description: str = "", harnesses: list[str] | None = None, ticket: str | None = None,
                 refs: list[str] | None = None, host: str = "", yes: bool = False, force: bool = False,
                 dry_run: bool = False, enable_pack: bool = False) -> int:
    from .importers import enable, next_steps, summary
    try:
        known = list(load_harnesses(include_disabled=True))
        for h in harnesses or []:
            if h not in known:
                raise ConfigError(f"--harness {h}: no such harness (known: {', '.join(known)})")
        given = {k for k, v in (("name", name), ("prefix", prefix), ("harnesses", harnesses),
                                ("ticket", ticket), ("refs", refs), ("host", host)) if v is not None and v != ""}
        a = Answers(name or "", prefix, pack_id, description,
                    harnesses if harnesses is not None else list(load_harnesses(include_missing=True)),
                    ticket or "none", refs or [], host)
        if not yes and sys.stdin.isatty():
            a = ask(a, given, known)
        elif not a.name:
            raise ConfigError(f"name the pack: `{config.command('new pack <name>')}`")
        if a.ticket == "none" and (refs or host):
            raise ConfigError("--refs and --host are for a ticket system: add --ticket github, jira or local")
        if host and a.ticket != "jira":
            raise ConfigError(f"--host is for --ticket jira, not {a.ticket}")
        spec = spec_for(a)
        files = render_pack(spec)
        dest = expand(to) if to else Path(a.name)
        dest = dest if dest.is_absolute() else Path.cwd() / dest
        check_dest(dest, files, force)
        tickets = f"{a.ticket} ({', '.join(spec.ticket['refs'])})" if spec.ticket else "none"
        print(f"Pack {spec.name}, prefix {spec.prefix}, for {', '.join(a.harnesses) or 'no harness'}; "
              f"tickets: {tickets}.")
        if dry_run:
            for rel in files:
                print(f"  would write {rel}")
            print(f"Would write {tilde(dest)}: {summary(spec, files)}.")
            if enable_pack:
                print(enable(spec.name, dest, dry_run=True))
            return 0
        write_pack(dest, files, force=force)
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    except OSError as e:
        print(f"ERROR {tilde(Path(e.filename)) + ': ' if e.filename else ''}{e.strerror or e}")
        return 1
    print(f"Wrote {tilde(dest)}: {summary(spec, files)}.")
    root = next((p for p in dest.parents if (p / ".git").exists()), None)
    if root and not (dest / ".git").exists():
        print(f"NOTE {tilde(dest)} is inside the repository {tilde(root)}, where its "
              f"{' and '.join(f'`{f}`' for f in ROOT_ONLY)} don't run: delete them and check the pack "
              "in that repository's CI (docs/packs/team-pack.md).")
    from .validate import cmd_validate
    code = cmd_validate(pack=str(dest))
    if code:
        return code
    return next_steps(spec.name, dest, enable_pack)
