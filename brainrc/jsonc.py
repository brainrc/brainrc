"""JSON with comments (OpenCode's opencode.jsonc): read it, and change one top-level key in place
so the user's comments and layout elsewhere in the file survive."""
from __future__ import annotations

import json
import re

PUNCT = "{}[],:"
LITERAL = re.compile(r"[^\s{}\[\],:/\"]+")


def _scan(text: str) -> tuple[list[tuple[str, int, int]], list[tuple[str, int, int]]]:
    """(tokens, comments), each as (text, start, end). Tokens are strings, punctuation and literals."""
    out, comments, i, n = [], [], 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end == -1 else end
            comments.append((text[i:end], i, end))
            i = end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                raise ValueError("unterminated comment")
            comments.append((text[i:end + 2], i, end + 2))
            i = end + 2
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise ValueError("unterminated string")
            out.append((text[i:j + 1], i, j + 1))
            i = j + 1
        elif c in PUNCT:
            out.append((c, i, i + 1))
            i += 1
        elif m := LITERAL.match(text, i):
            out.append((m[0], i, m.end()))
            i = m.end()
        else:
            raise ValueError(f"unexpected {c!r}")
    return out, comments


def _tokens(text: str) -> list[tuple[str, int, int]]:
    return _scan(text)[0]


def loads(text: str):
    """Parse JSONC: comments and trailing commas allowed."""
    toks = _tokens(text)
    kept = [t for k, t in enumerate(toks)
            if not (t[0] == "," and k + 1 < len(toks) and toks[k + 1][0] in "}]")]
    return json.loads(" ".join(t[0] for t in kept))


def _members(toks) -> tuple[list[tuple[str, int, int, int]], int]:
    """The root object's members as (key, key token index, value start index, value end index),
    and the index of its closing brace. Raises ValueError unless the root is an object."""
    if not toks or toks[0][0] != "{":
        raise ValueError("not a JSON object")
    members, k = [], 1
    while toks[k][0] != "}":
        if toks[k][0] == ",":
            k += 1
            continue
        if not toks[k][0].startswith('"') or toks[k + 1][0] != ":":
            raise ValueError("expected a key")
        key, start, depth, j = json.loads(toks[k][0]), k + 2, 0, k + 2
        while True:
            t = toks[j][0]
            depth += t in "{[" and len(t) == 1
            depth -= t in "}]" and len(t) == 1
            if depth < 0 or (depth == 0 and t == ","):
                break
            j += 1
        members.append((key, k, start, j - 1))
        k = j
    return members, k


def _cut_before(text: str, prev_end: int, key_start: int) -> int:
    """Where removing a member that starts at key_start begins: its line's start (the newline
    before it) when only indentation precedes it there, else the key itself, so a comment above it
    or before it on its line stays; on a line shared with the previous member, right after that."""
    gap = text[prev_end:key_start]
    if not gap.strip() and "\n" not in gap:
        return prev_end
    nl = text.rfind("\n", prev_end, key_start)
    return nl if nl != -1 and not text[nl + 1:key_start].strip() else key_start


def _set_key(text: str, key: str, value) -> tuple[str, tuple[int, int]]:
    """set_key's result, and the span of text it replaced (so comments in it may go)."""
    toks = _tokens(text)
    members, close = _members(toks)
    found = [m for m in members if m[0] == key]
    indent = "  "
    if members:
        first = toks[members[0][1]][1]
        lead = text[text.rfind("\n", 0, first) + 1:first]
        indent = lead if lead and lead.isspace() else indent
    rendered = json.dumps(value, indent=2).replace("\n", "\n" + indent)
    if found:
        _, k, vs, ve = found[-1]
        if value is not None:
            span = (toks[vs][1], toks[ve][2])
            return text[:span[0]] + rendered + text[span[1]:], span
        prev, after = toks[k - 1], ve + 1
        cut = _cut_before(text, prev[2], toks[k][1])
        if toks[after][0] == ",":
            return text[:cut] + text[toks[after][2]:], (toks[k][1], toks[after][2])
        if prev[0] == ",":  # the last member: its comma goes too
            return text[:prev[1]] + text[prev[2]:cut] + text[toks[ve][2]:], (toks[k][1], toks[ve][2])
        return text[:cut] + text[toks[ve][2]:], (toks[k][1], toks[ve][2])
    if value is None:
        return text, (0, 0)
    last, end = toks[close - 1], toks[close][1]
    line = text.rfind("\n", last[2], end) + 1  # the closing brace's own line, if it has one
    at, entry = (line, "") if line and not text[line:end].strip() else (end, "\n")
    entry += f"{indent}{json.dumps(key)}: {rendered}\n"
    sep = "" if last[0] in "{," else ","
    return text[:last[2]] + sep + text[last[2]:at].rstrip(" \t") + entry + text[at:], (0, 0)


def set_key(text: str, key: str, value) -> str:
    """text with the root object's `key` set to value (removed when value is None). Every comment
    outside what it replaces stays; raises ValueError if one wouldn't."""
    out, (start, end) = _set_key(text, key, value)
    kept = [c[0] for c in _scan(text)[1] if not start <= c[1] < end]
    if [c[0] for c in _scan(out)[1]] != kept:
        raise ValueError("the edit would lose a comment")
    return out
