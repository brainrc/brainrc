"""Split a markdown instructions file into ordered rules, one per section."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..scaffold import Rule, slugify

HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)[ \t#]*$")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")


@dataclass
class Section:
    title: str
    first: int  # 1-based line numbers in the source, inclusive
    last: int
    text: str


def fenced(lines: list[str]) -> list[bool]:
    """For each line, whether it is part of a fenced code block (its fence lines included), as
    CommonMark reads fences: a closing fence uses the opening's character, at least as many."""
    out, fence = [], ""
    for line in lines:
        m = FENCE_OPEN.match(line)
        if fence:
            out.append(True)
            if m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not line.strip()[len(m[1]):].strip():
                fence = ""
            continue
        if m and not (m[1][0] == "`" and "`" in line.strip()[len(m[1]):]):
            fence = m[1]
        out.append(bool(fence))
    return out


def headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(index, level, title) of every ATX heading outside a fenced code block."""
    found = []
    for i, (line, in_fence) in enumerate(zip(lines, fenced(lines))):
        if not in_fence and (h := HEADING.match(line)):
            found.append((i, len(h[1]), h[2]))
    return found


def split(text: str, first_line: int = 1) -> list[Section]:
    """Sections at the shallowest heading level used more than once (so a lone title stays with
    the text under it), each with its line range. Text before the first such heading is its own
    section. Blank lines between sections are dropped; everything else is kept as written."""
    lines = text.splitlines()
    found = headings(lines)
    levels = [lvl for _, lvl, _ in found]
    level = next((lvl for lvl in sorted(set(levels)) if levels.count(lvl) >= 2), None)
    starts = [(i, title) for i, lvl, title in found if lvl == level]
    if not starts or starts[0][0] != 0:
        starts.insert(0, (0, ""))
    sections = []
    for n, (start, title) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        chunk = lines[start:end]
        lead = next((k for k, line in enumerate(chunk) if line.strip()), None)
        if lead is None:
            continue
        tail = max(k for k, line in enumerate(chunk) if line.strip())
        if not title:  # the text before the first heading: name it by its own title, if it has one
            title = next((t for i, _, t in found if start <= i < end), "")
        sections.append(Section(title, first_line + start + lead, first_line + start + tail,
                                "\n".join(chunk[lead:tail + 1])))
    return sections


def to_rules(sections: list[Section], label: str, fallback: str = "rules") -> list[Rule]:
    return [Rule(slugify(s.title, fallback), s.text,
                 f"imported by brainrc from {label}, lines {s.first}-{s.last}") for s in sections]


def provenance(origins: list[tuple[str, int]]) -> str:
    """`imported by brainrc from A, lines 1-4; B, lines 1-9` for lines that came from several files."""
    runs: list[list] = []
    for label, n in origins:
        if runs and runs[-1][0] == label and n == runs[-1][2] + 1:
            runs[-1][2] = n
        else:
            runs.append([label, n, n])
    return "imported by brainrc from " + "; ".join(f"{label}, lines {a}-{b}" for label, a, b in runs)


def rules_from_lines(lines: list[tuple[str, int, str]], fallback: str) -> list[Rule]:
    """Rules from (file label, line number, text) lines that may come from several files (inlined
    imports): split as one text, each rule naming the files and lines it holds."""
    sections = split("\n".join(text for _, _, text in lines))
    return [Rule(slugify(s.title, fallback), s.text,
                 provenance([(label, n) for label, n, _ in lines[s.first - 1:s.last]]))
            for s in sections]


def simple_frontmatter(text: str) -> tuple[dict[str, str], int]:
    """`key: value` frontmatter as Cursor and Copilot write it (`globs: *.ts` is not valid YAML, so no
    YAML parser), and the index of the first body line."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, 0
    meta = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return meta, i + 1
        key, sep, value = line.partition(":")
        if sep and key.strip():
            meta[key.strip()] = value.strip()
    return {}, 0  # never closed: all of it is body


def unquote(value: str) -> str:
    value = value.strip()
    return value[1:-1] if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'" else value


def globs(value: str) -> list[str]:
    """`*.py, scripts/**/*.py`, `"**/*.ts,**/*.tsx"` or `["src/**/*.tsx", ...]` -> the globs."""
    value = unquote(value)
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [g for g in (unquote(part) for part in value.split(",")) if g]


def whole_body(text: str) -> tuple[dict[str, str], str, int, int] | None:
    """(frontmatter, body, first line, last line) of a rule file kept whole, or None when it has
    no text after its frontmatter."""
    meta, start = simple_frontmatter(text)
    lines = text.splitlines()
    sections = split("\n".join(lines[start:]), start + 1)
    if not sections:
        return None
    first, last = sections[0].first, sections[-1].last
    return meta, "\n".join(lines[first - 1:last]), first, last
