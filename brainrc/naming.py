"""Pack naming rules (docs/packs.md#naming), checked by validate and before apply links a pack."""
from __future__ import annotations

import re

from .config import ConfigError, KINDS
from .mcp import REGISTRY, _registry
from .sources import Source, frontmatter, item_name, items, markdown_files

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")  # rule 5; use fullmatch (`$` would allow a newline)
PACK_ID = re.compile(r"([a-z0-9]+(?:-[a-z0-9]+)*)/([a-z0-9]+(?:-[a-z0-9]+)*)")
OFFICIAL = "brainrc"
# The official pack IDs, as listed in docs/packs.md § Naming.
OFFICIAL_PACK_IDS = frozenset({
    "brainrc/starter", "brainrc/review", "brainrc/go", "brainrc/terraform-aws",
    "brainrc/kubernetes", "brainrc/security-baseline",
})
# Rule 3: names only a verified vendor's own packs may use.
VENDOR_NAMES = frozenset({
    "amazon", "anthropic", "atlassian", "aws", "azure", "chatgpt", "claude", "copilot", "cursor",
    "docker", "gemini", "github", "gitlab", "google", "hashicorp", "jetbrains", "microsoft",
    "openai", "slack", "windsurf",
})
# Owner handle -> the vendor names its packs may use. Filled by the verified vendor program (#333).
VERIFIED_VENDORS: dict[str, frozenset[str]] = {}
PREFIX_MIN, PREFIX_MAX = 2, 24  # rule 6, not counting the trailing hyphen


def edits(a: str, b: str) -> int:
    """Edit distance where a swap of two neighbours counts as one edit (`brianrc` is one from `brainrc`)."""
    prev2, prev = [], list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[-1]


def _reserved(value: str) -> bool:
    return value == OFFICIAL or value.startswith((f"{OFFICIAL}-", f"{OFFICIAL}/"))


def check_pack_names(src: Source) -> list[str]:
    where = f"{src.name}:pack.toml"
    stem = src.prefix[:-1] if src.prefix.endswith("-") else src.prefix
    errors = []
    if not NAME.fullmatch(src.name):
        errors.append(f"{where}: `name` must be ASCII lowercase letters, digits and hyphens")
    if not src.prefix.endswith("-") or not NAME.fullmatch(stem):
        errors.append(f"{where}: `prefix` must be ASCII lowercase letters, digits and hyphens, ending with '-'")
    elif not PREFIX_MIN <= len(stem) <= PREFIX_MAX:
        errors.append(f"{where}: `prefix` `{src.prefix}` must be {PREFIX_MIN} to {PREFIX_MAX} characters "
                      "before its '-'")
    pack_id = src.meta.get("id")
    if pack_id is not None and not (isinstance(pack_id, str) and PACK_ID.fullmatch(pack_id)):
        errors.append(f"{where}: `id` must be `<owner>/<pack>` in ASCII lowercase letters, digits and hyphens")
        pack_id = None
    owner = pack_id.split("/")[0] if pack_id else ""
    if owner and not src.prefix.startswith(f"{owner}-"):
        errors.append(f"{where}: `prefix` `{src.prefix}` must start with the owner handle `{owner}-` from `id`")
    official = pack_id in OFFICIAL_PACK_IDS
    if official:
        return errors + _item_names(src)
    fields = [("name", src.name), ("prefix", src.prefix)] + ([("id", pack_id)] if pack_id else [])
    vendors = VENDOR_NAMES - VERIFIED_VENDORS.get(owner, frozenset())
    for key, value in fields:
        if _reserved(value):
            errors.append(f"{where}: `{key}` `{value}`: `brainrc-` and `brainrc/` are reserved for official packs")
        for vendor in sorted(set(re.split(r"[-/]", value)) & vendors):
            errors.append(f"{where}: `{key}` `{value}` uses the vendor name `{vendor}`; only that vendor's "
                          "verified packs may")
    # Rule 4: the whole name and its first word, so `brainrx-tools` is caught as well as `brainrx`.
    looks = {src.name, stem, src.name.split("-")[0], stem.split("-")[0], owner} - {""}
    errors += [f"{where}: `{n}` is one or two edits from the official name `{OFFICIAL}`"
               for n in sorted(looks) if 1 <= edits(n, OFFICIAL) <= 2]
    errors += [f"{where}: `id` `{pack_id}` is one or two edits from the official pack `{o}`"
               for o in sorted(OFFICIAL_PACK_IDS) if pack_id and 1 <= edits(pack_id, o) <= 2]
    return errors + _item_names(src)


def _item_names(src: Source) -> list[str]:
    """Rule 5 for agents, commands and MCP servers (skills already have their own name check)."""
    errors = [f"{src.rel(p)}: name must be ASCII lowercase letters, digits and hyphens"
              for kind in KINDS if kind != "skills" for p in items(src, kind) if not NAME.fullmatch(item_name(p))]
    try:
        servers = _registry(src)
    except ConfigError:
        return errors  # check_servers reports it
    errors += [f"{src.rel(src.root / REGISTRY)}: server `{n}`: name must be ASCII lowercase letters, digits "
               "and hyphens" for n in servers if not NAME.fullmatch(n)]
    return errors


# Core agents moved under `brainrc-` (gh:295); the old names stay as aliases for one minor release.
AGENT_ALIASES = {n: f"brainrc-{n}" for n in (
    "analyst", "architect", "code-reviewer", "doc-writer", "implementer", "infra-reviewer",
    "researcher", "security-reviewer", "test-writer", "verifier")}
AGENT_ALIAS_REMOVED_IN = "0.7.0"


def check_core_agents(src: Source) -> list[str]:
    """Every core agent is `brainrc-*` or a declared alias that runs as its target until removal."""
    errors = [f"{src.rel(f)}: core agent names start with `brainrc-`"
              for f in markdown_files("agents", src)
              if not f.stem.startswith("brainrc-") and f.stem not in AGENT_ALIASES]
    for old, new in AGENT_ALIASES.items():
        path, target = src.root / "agents" / f"{old}.md", src.root / "agents" / f"{new}.md"
        rel = src.rel(path)
        if not path.is_file():
            errors.append(f"{rel}: deprecated alias for `{new}` is missing (keep it until {AGENT_ALIAS_REMOVED_IN})")
            continue
        if not target.is_file():
            errors.append(f"{rel}: alias target `{new}` is missing")
            continue
        meta, want = frontmatter(path), frontmatter(target)
        if not meta.get("description", "").lower().startswith("deprecated"):
            errors.append(f"{rel}: alias `description` must start with `Deprecated`")
        errors += [f"{rel}: alias `{key}` must match `{new}` so it runs with the same access"
                   for key in ("tools", "model") if meta.get(key) != want.get(key)]
        body = path.read_text().split("\n---\n", 1)[-1]
        if f"`{new}`" not in body:
            errors.append(f"{rel}: alias body must name `{new}`")
        if AGENT_ALIAS_REMOVED_IN not in body:
            errors.append(f"{rel}: alias body must name the removal release {AGENT_ALIAS_REMOVED_IN}")
    return errors
