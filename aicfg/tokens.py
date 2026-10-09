"""Context cost estimates and always-loaded budgets."""
from __future__ import annotations

from pathlib import Path

from .config import ConfigError
from .sources import (
    Source,
    _markdown_under,
    frontmatter,
    items,
    markdown_files,
    render_instructions,
    rule_text,
    skills,
    sources,
)


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4  # ~4 chars per token; good enough to compare sizes


CORE_ALWAYS_BUDGET = 3000     # tokens core may load into every session (rules + descriptions)


PACK_WARN_TOKENS = 1000       # a pack without max_always_tokens gets a warning above this


DESCRIPTION_WARN_TOKENS = 100


def _description_tokens(path: Path) -> int:
    return estimate_tokens(frontmatter(path).get("description", ""))


def always_tokens(src: Source) -> tuple[int, list[tuple[int, str]]]:
    """What a source loads into every session: its rules, and each item's description."""
    items = [(estimate_tokens(rule_text(p)), src.rel(p)) for p in markdown_files("rules", src)]
    items += [(_description_tokens(s / "SKILL.md"), src.rel(s)) for s in skills(src)]
    items += [(_description_tokens(f), src.rel(f)) for kind in ("agents", "commands")
              for f in markdown_files(kind, src)]
    return sum(n for n, _ in items), items


def source_budget(src: Source) -> int | None:
    return CORE_ALWAYS_BUDGET if src.is_core else src.meta.get("max_always_tokens")


def check_budgets(srcs: list[Source]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for src in srcs:
        total, items = always_tokens(src)
        biggest = ", ".join(f"{label} {n}" for n, label in sorted(items, reverse=True)[:3])
        budget = source_budget(src)
        if budget is not None and total > budget:
            errors.append(f"{src.name}: ~{total} always-loaded tokens, budget {budget} (biggest: {biggest})")
        elif budget is None and total > PACK_WARN_TOKENS:
            warnings.append(f"{src.name}: ~{total} always-loaded tokens and no `max_always_tokens` in "
                            f"pack.toml (biggest: {biggest})")
        for f in [s / "SKILL.md" for s in skills(src)] + [f for k in ("agents", "commands")
                                                         for f in markdown_files(k, src)]:
            n = _description_tokens(f)
            if n > DESCRIPTION_WARN_TOKENS:
                label = src.rel(f.parent if f.name == "SKILL.md" else f)
                warnings.append(f"{label}: description is ~{n} tokens (over {DESCRIPTION_WARN_TOKENS})")
    return errors, warnings


def cmd_tokens() -> int:
    """Context cost per item. `always` loads in every session; `on use` only when triggered."""
    try:
        srcs = sources()
    except ConfigError as e:
        print(f"ERROR {e}")
        return 1
    rows: list[tuple[int, int, str]] = []  # (on-use tokens, always tokens, label)
    for src in srcs:
        tag = "" if src.is_core else f"{src.name}:"
        for s in skills(src):
            body = estimate_tokens((s / "SKILL.md").read_text())
            refs = sum(estimate_tokens(p.read_text()) for p in _markdown_under(s) if p.name != "SKILL.md")
            description = estimate_tokens(frontmatter(s / "SKILL.md").get("description", ""))
            rows.append((body + refs, description, f"{tag}skills/{s.name} (SKILL.md {body}, refs {refs})"))
        for kind in ("agents", "commands"):
            for f in markdown_files(kind, src):
                description = estimate_tokens(frontmatter(f).get("description", ""))
                rows.append((estimate_tokens(f.read_text()), description, f"{tag}{kind}/{f.name}"))
    instructions = estimate_tokens(render_instructions(srcs))
    print(f"{'on use':>7} {'always':>7}  item")
    for on_use, always, label in sorted(rows, reverse=True):
        print(f"{on_use:7} {always:7}  {label}")
    always_total = instructions + sum(r[1] for r in rows)
    print(f"\nAlways loaded: ~{always_total} tokens (rules {instructions}, descriptions "
          f"{always_total - instructions}). On use: ~{sum(r[0] for r in rows)} tokens if everything loads.")
    for src in srcs:
        budget = source_budget(src)
        print(f"{src.name}: ~{always_tokens(src)[0]} / {budget if budget is not None else 'no budget'} "
              "always-loaded tokens")
    return 0
